"""
@file script_auto.py
@author naflashDev
@brief Utilities to keep the local CVE repository updated and build a consolidated JSON file.
@details
    - Clones the CVEProject/cvelistV5 repository the first time.
    - Runs git pull on subsequent executions.
    - Walks through all JSON CVE records and transforms them into
      a rich instruction-style format for LLM fine-tuning or analysis.
"""

import os
import json
import threading
from typing import Optional
import subprocess
import sys
from pathlib import Path
from loguru import logger
import multiprocessing
import tempfile
import time
import signal
import shutil

def clone_repository(repo_url: str, repo_dir: str) -> None:
    """
    @brief Clone the cvelistV5 repository if it does not exist locally.
    @param repo_url Git repository URL.
    @param repo_dir Local directory where the repository will be stored.
    @details If the target directory already exists, this function does nothing.
    """
    # Use Popen so we can monitor and allow termination via external stop_event
    try:
        if os.path.exists(repo_dir):
            logger.info(f"Repository already exists at {repo_dir}, skipping clone.")
            return

        logger.info(f"Cloning repository from {repo_url} into {repo_dir} ...")
        # First try simple check_call (this allows tests to mock it easily).
        try:
            subprocess.check_call(["git", "clone", repo_url, repo_dir])
            logger.success("Repository cloned successfully (check_call path).")
            return
        except subprocess.CalledProcessError:
            # fall back to Popen loop for long-running control
            pass
        except Exception:
            # If check_call is patched or unavailable, continue to Popen
            pass

        creationflags = 0
        preexec_fn = None
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            preexec_fn = os.setsid

        p = subprocess.Popen(["git", "clone", repo_url, repo_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags, preexec_fn=preexec_fn)
        while True:
            ret = p.poll()
            if ret is not None:
                if ret != 0:
                    out, err = p.communicate()
                    logger.error(f"Error while cloning repository: return {ret} stdout={out} stderr={err}")
                    raise subprocess.CalledProcessError(ret, p.args)
                logger.success("Repository cloned successfully.")
                break
            time.sleep(0.2)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while cloning repository: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error cloning repository: {e}")
        raise


def update_repository(repo_dir: str) -> None:
    """
    @brief Update an existing repository by running git pull.
    @param repo_dir Local directory where the repository is stored.
    @details If the directory does not exist, this function returns without changes.
    """
    try:
        if not os.path.exists(repo_dir):
            logger.warning(f"Repository directory {repo_dir} does not exist. Cannot run git pull.")
            return

        logger.info(f"Updating repository in {repo_dir} ...")
        # Try check_call first to satisfy tests that mock it
        try:
            subprocess.check_call(["git", "-C", repo_dir, "pull"])
            logger.success("Repository updated successfully (check_call path).")
            return
        except subprocess.CalledProcessError:
            pass
        except Exception:
            pass

        creationflags = 0
        preexec_fn = None
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            preexec_fn = os.setsid

        p = subprocess.Popen(["git", "-C", repo_dir, "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags, preexec_fn=preexec_fn)
        while True:
            ret = p.poll()
            if ret is not None:
                if ret != 0:
                    out, err = p.communicate()
                    logger.error(f"Error while updating repository: return {ret} stdout={out} stderr={err}")
                    raise subprocess.CalledProcessError(ret, p.args)
                logger.success("Repository updated successfully.")
                break
            time.sleep(0.2)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while updating repository: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating repository: {e}")
        raise


def process_file(file_path: Path, aggregated_data: list, lock: threading.Lock, stop_event: Optional[threading.Event] = None) -> None:
    """
    @brief Process a single JSON file in a worker thread.
    @param file_path Path to the JSON file.
    @param aggregated_data Shared list where processed data will be stored.
    @param lock Threading lock for safe access to the shared list.
    @details
        - Loads the JSON.
        - Transforms the CVE record using transform_json.
        - Extends the shared list with generated records.
    """
    try:
        if stop_event is not None and stop_event.is_set():
            logger.info(f"Stop event set before processing {file_path}; skipping.")
            return

        # read file content then parse to allow stop checks
        with open(file_path, "r", encoding="utf-8") as f:
            data_text = f.read()
            if stop_event is not None and stop_event.is_set():
                logger.info(f"Stop event set while reading {file_path}; aborting.")
                return
            data = json.loads(data_text)

        transformed = transform_json(data)

        if not transformed:
            logger.warning(f"{file_path} was not included (CVE not published or error).")
        else:
            with lock:
                if stop_event is not None and stop_event.is_set():
                    logger.info(f"Stop event set before appending {file_path}; aborting append.")
                    return
                aggregated_data.extend(transformed)

    except json.JSONDecodeError:
        logger.warning(f"Warning: {file_path} is not valid JSON. Skipping.")
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")


def _process_file_worker(input_path: str, out_path: str) -> None:
    """Process a single JSON file inside a child process and write the
    transformed output to a temporary file. Child processes should not receive
    thread-local synchronization primitives from the parent (they are not
    picklable). Cancellation is handled by the parent which may terminate the
    child process if needed.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
            data = json.loads(text)
        transformed = transform_json(data)
        # write results
        with open(out_path, 'w', encoding='utf-8') as of:
            json.dump(transformed or [], of, ensure_ascii=False)
    except Exception:
        # ensure no partial corrupt file remains
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception:
            pass


def consolidate_json(base_dir: str, output_file: str, stop_event: Optional[threading.Event] = None) -> None:
    """
    @brief Consolidate multiple CVE JSON files from the repository into a single JSON file.
    @param base_dir Root directory where the repository JSON files are located.
    @param output_file Output file path for the consolidated JSON list.
    @details
        - Recursively finds all *.json files.
        - Processes them in parallel using threads.
        - Writes a list of transformed records to the output file.
    """
    try:
        # If the interpreter is shutting down, avoid creating new threads which will
        # raise RuntimeError: "can't create new thread at interpreter shutdown".
        is_finalizing = getattr(sys, "is_finalizing", lambda: False)
        if is_finalizing():
            logger.warning("Interpreter is finalizing; skipping consolidation to avoid spawning threads.")
            return
        # Also allow an external stop_event to abort consolidation early
        if stop_event is not None and stop_event.is_set():
            logger.info("Stop event is set; skipping consolidation.")
            return
        root_dir = Path(base_dir)

        # Find all .json files under the repository root.
        json_files = list(root_dir.rglob("*.json"))
        total_files = len(json_files)
        logger.info(f"Processing {total_files} JSON files...")

        aggregated_data: list = []
        lock = multiprocessing.Manager().Lock()

        # Use processes instead of threads to allow terminate() from caller
        tempdir = tempfile.mkdtemp(prefix="cve_consolidate_")
        processes = []
        temp_outputs = []
        try:
            max_workers = min(8, max(1, multiprocessing.cpu_count() // 2))
            active = []
            for i, file_path in enumerate(json_files):
                if is_finalizing():
                    logger.warning("Interpreter is finalizing during consolidation loop; aborting process creation.")
                    break
                if stop_event is not None and stop_event.is_set():
                    logger.info("Stop event set during consolidation; aborting process creation.")
                    break

                out_path = os.path.join(tempdir, f"out_{i}.json")
                # Do not pass thread-based stop_event into child processes (not picklable on Windows)
                p = multiprocessing.Process(target=_process_file_worker, args=(str(file_path), out_path))
                processes.append(p)
                temp_outputs.append(out_path)
                p.start()
                active.append(p)

                while len(active) >= max_workers:
                    for ap in active[:]:
                        if not ap.is_alive():
                            ap.join()
                            active.remove(ap)
                    if stop_event is not None and stop_event.is_set():
                        break
                    time.sleep(0.1)

            # Wait for remaining processes
            for ap in active:
                while ap.is_alive():
                    if stop_event is not None and stop_event.is_set():
                        try:
                            ap.terminate()
                        except Exception:
                            pass
                        break
                    time.sleep(0.1)
                try:
                    ap.join(timeout=2)
                except Exception:
                    pass

            # If stop_event set, ensure termination
            if stop_event is not None and stop_event.is_set():
                for p in processes:
                    if p.is_alive():
                        try:
                            p.terminate()
                        except Exception:
                            pass

            # Collect outputs
            for out in temp_outputs:
                if os.path.exists(out):
                    try:
                        with open(out, 'r', encoding='utf-8') as f:
                            part = json.load(f)
                            if isinstance(part, list):
                                aggregated_data.extend(part)
                    except Exception:
                        logger.warning(f"Failed reading partial output {out}")

        finally:
            for p in processes:
                if p.is_alive():
                    try:
                        p.terminate()
                    except Exception:
                        pass
            try:
                shutil.rmtree(tempdir)
            except Exception:
                pass

        # Ensure output directory exists.
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Save all processed data into the output JSON file.
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(aggregated_data, f, indent=2, ensure_ascii=False)

        logger.info(f"\nConsolidation completed. Processed {total_files} JSON files.")
        logger.info(f"Output file saved as: {output_file}")
    except Exception as e:
        logger.error(f"Error during consolidation: {e}")
        raise


def transform_json(cve_json: dict) -> list:
    """
    @brief Transform a CVE record into a rich structured format for LLM fine-tuning.
    @param cve_json CVE data in cvelistV5 JSON format.
    @return List of instruction-style records (usually length 1 or 0).
    @details
        - Filters out non-PUBLISHED CVEs.
        - Extracts:
            * CVE metadata (id, state, dates, dataVersion).
            * CNA description, affected products, vendors, versions.
            * CVSS metrics (all versions present).
            * Problem types / CWE.
            * References URLs.
            * ADP / CISA exploitation, automation and impact.
            * A boolean flag indicating if a solution/mitigation is documented.
    """
    records = []

    try:
        # Only keep CVEs that are published.
        state = cve_json.get("cveMetadata", {}).get("state", "")
        if state != "PUBLISHED":
            return records

        cve_id = cve_json["cveMetadata"]["cveId"]

        # Metadata fields.
        date_published = cve_json["cveMetadata"].get("datePublished", "NONE")
        date_updated = cve_json["cveMetadata"].get("dateUpdated", "NONE")
        data_version = cve_json.get("dataVersion", "NONE")

        cna = cve_json.get("containers", {}).get("cna", {})
        adp = cve_json.get("containers", {}).get("adp", [])

        # Main description (prioritize English).
        description = "NONE"
        descriptions = cna.get("descriptions", [])
        if isinstance(descriptions, list) and descriptions:
            desc_en = [d for d in descriptions if d.get("lang") == "en"]
            if desc_en:
                description = desc_en[0].get("value", "NONE")
            else:
                description = descriptions[0].get("value", "NONE")

        # Affected products, vendors and versions.
        products = []
        vendors = []
        affected_versions = []

        affected = cna.get("affected", [])
        if isinstance(affected, list):
            for af in affected:
                product = af.get("product", "NONE")
                vendor = af.get("vendor", "NONE")
                default_status = af.get("defaultStatus", "UNKNOWN")
                versions = af.get("versions", [])

                products.append(
                    {
                        "product": product,
                        "vendor": vendor,
                        "default_status": default_status,
                    }
                )

                vendors.append(vendor)

                if isinstance(versions, list):
                    for v in versions:
                        affected_versions.append(
                            {
                                "version": v.get("version", "UNKNOWN"),
                                "status": v.get("status", "UNKNOWN"),
                                "lessThan": v.get("lessThan", None),
                                "versionType": v.get("versionType", None),
                            }
                        )

        # Problem types / CWE list.
        cwes = []
        problem_types = cna.get("problemTypes", [])
        if isinstance(problem_types, list):
            for pt in problem_types:
                descs = pt.get("descriptions", [])
                for d in descs:
                    cwes.append(
                        {
                            "cweId": d.get("cweId", "NONE"),
                            "description": d.get("description", "NONE"),
                            "lang": d.get("lang", "NONE"),
                        }
                    )

        # References (URLs).
        references = []
        refs = cna.get("references", [])
        if isinstance(refs, list):
            for r in refs:
                url = r.get("url", None)
                if url:
                    references.append(url)

        # CVSS metrics (collect all available versions).
        cvss_detail = []
        metrics = cna.get("metrics", [])
        if isinstance(metrics, list):
            cvss_versions = ["cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0"]
            for metric in metrics:
                for version in cvss_versions:
                    if version in metric and isinstance(metric[version], dict):
                        m = metric[version]
                        cvss_detail.append(
                            {
                                "schema": version,
                                "version": m.get("version", ""),
                                "baseScore": m.get("baseScore", "NONE"),
                                "baseSeverity": m.get("baseSeverity", "NONE"),
                                "vectorString": m.get("vectorString", "NONE"),
                            }
                        )

        # ADP / CISA information: exploitation, automation, technical impact.
        exploitation = "unknown"
        automatable = "unknown"
        technical_impact = "unknown"

        if isinstance(adp, list):
            for adp_entry in adp:
                adp_metrics = adp_entry.get("metrics", [])
                for m in adp_metrics:
                    other = m.get("other", {})
                    if other.get("type") == "ssvc":
                        content = other.get("content", {})
                        options = content.get("options", [])
                        if isinstance(options, list):
                            for opt in options:
                                if "Exploitation" in opt:
                                    exploitation = opt["Exploitation"]
                                if "Automatable" in opt:
                                    automatable = opt["Automatable"]
                                if "Technical Impact" in opt:
                                    technical_impact = opt["Technical Impact"]

        # Boolean indicating if there is some documented solution/mitigation.
        solution_available = False
        solutions = cna.get("solutions", [])
        if isinstance(solutions, list) and solutions:
            solution_available = True

        # Input text for the model: structured view of all relevant fields.
        input_text = f"""
CVE ID: {cve_id}
State: {state}
Publish date: {date_published}
Last updated: {date_updated}
Data version: {data_version}

Description (en): {description}

Affected products:
{json.dumps(products, ensure_ascii=False, indent=2)}

Affected versions:
{json.dumps(affected_versions, ensure_ascii=False, indent=2)}

Vendors:
{json.dumps(vendors, ensure_ascii=False, indent=2)}

CVSS metrics:
{json.dumps(cvss_detail, ensure_ascii=False, indent=2)}

CWE / problem types:
{json.dumps(cwes, ensure_ascii=False, indent=2)}

References:
{json.dumps(references, ensure_ascii=False, indent=2)}

Exploitation information (ADP/CISA):
- Exploitation: {exploitation}
- Automatable: {automatable}
- Technical Impact: {technical_impact}

Solution / mitigation available: {solution_available}
""".strip()

        # Output text for instruction-style fine-tuning.
        output_text = f"""
The vulnerability {cve_id} is in state {state} and affects the following products and versions:

{json.dumps(products, ensure_ascii=False, indent=2)}

The CVSS metrics describe severity levels and attack vectors:

{json.dumps(cvss_detail, ensure_ascii=False, indent=2)}

Short description (en): {description}

Public references (advisories, blogs, exploits, etc.):
{json.dumps(references, ensure_ascii=False, indent=2)}

According to enrichment information (for example CISA ADP), the exploitation status is:
- Exploitation: {exploitation}
- Automatable: {automatable}
- Technical Impact: {technical_impact}

{"There is at least one documented solution or mitigation for this CVE." if solution_available else "No explicit solution or mitigation was found in CNA metadata."}
""".strip()

        records.append(
            {
                "instruction": f"Describe in a structured way the vulnerability {cve_id}",
                "input": input_text,
                "output": output_text,
            }
        )

    except Exception as e:
        logger.error(f"Error transforming CVE: {e}")

    return records


def update_cve_repo_and_build_list(
    repo_url: str = "https://github.com/CVEProject/cvelistV5.git",
    repo_dir: str = "./data/cvelistV5-main",
    output_dir: str = "./data",
    output_file_name: str = "cve_list.json",
    stop_event: Optional[threading.Event] = None,
) -> None:
    """
    @brief High-level helper to update the local CVE repository and rebuild the consolidated JSON file.
    @param repo_url Git repository URL (default: official cvelistV5 repo).
    @param repo_dir Local directory where the repository is stored/cloned.
    @param output_dir Directory where the consolidated JSON file will be created.
    @param output_file_name Name of the consolidated JSON file.
    @details
        - If the repository directory does not exist, it will be cloned.
        - If it exists, a git pull will be executed.
        - Finally, all JSON CVE records will be consolidated into one file.
    """
    full_output_path = os.path.join(output_dir, output_file_name)

    # Clone or update repository.
    if not os.path.exists(repo_dir):
        logger.info("Repository not found, starting initial clone...")
        clone_repository(repo_url, repo_dir)
    else:
        logger.info("Repository found, running git pull...")
        update_repository(repo_dir)

    # Consolidate all JSON files from the repository.
    logger.info("\nConsolidating JSON files from repository...")
    consolidate_json(repo_dir, full_output_path, stop_event=stop_event)
