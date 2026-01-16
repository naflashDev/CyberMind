# Auditoría de f-strings

Se han detectado las siguientes ocurrencias de `f-strings` en el código fuente. Revisar manualmente y, cuando interpolen datos externos, convertir a logging parametrizado o sanitizar entradas.


## Resumen

Total ocurrencias: 155


## Detalles

- src\main.py [L203]: retorno_otros = create_config_file(file_name, file_content + [f"{default_parameters[0]};{default_parameters[1]}\n"])

- src\main.py [L393]: logger.info(f"Mounting UI static files from {STATIC_DIR}")

- src\main.py [L446]: logger.warning(f"UI static directory not found at {STATIC_DIR}; UI will not be served from main.py")

- src\app\models\opensearh_db.py [L29]: logger.info(f"Connecting to OpenSearch instance at {host}:{port}.")

- src\app\models\opensearh_db.py [L38]: f"Document indexed successfully. Response: {response['result']}"

- src\app\models\opensearh_db.py [L42]: logger.error(f"Error while storing data in OpenSearch: {e}")

- src\app\models\opensearh_db.py [L82]: logger.error(f"No existe el indice: {e}")

- src\app\models\opensearh_db.py [L123]: logger.info(f"Index '{index_name}' created in OpenSearch.")

- src\app\models\opensearh_db.py [L125]: logger.error(f"Error checking/creating index '{index_name}': {e}")

- src\app\models\ttrss_postgre_db.py [L89]: detail=f"Error al insertar el feed en la base de datos: {str(e)}"

- src\app\utils\run_services.py [L36]: cmd_list = ["docker", "ps", "--filter", f"name={container_name}", "--filter", "status=running", "--format", "{{.Names}}"]

- src\app\utils\run_services.py [L43]: context = f"WSL distro '{distro_name}'"

- src\app\utils\run_services.py [L217]: cfg_cmd = base_compose + ["-f", str(cf_path), "config", "--services"]

- src\app\utils\run_services.py [L231]: cmd = base_compose + ["-f", str(tinytinyrss_file), "-f", str(opensearch_file)]

- src\app\utils\run_services.py [L249]: check_cmd = ["docker", "ps", "-a", "--filter", f"label=com.docker.compose.service={svc_name}", "--format", "{{.Names}}"]

- src\app\utils\run_services.py [L265]: cmd = base_compose + ["-f", str(tinytinyrss_file), "-f", str(opensearch_file)]

- src\app\utils\run_services.py [L283]: cmd = base_compose + ["-f", str(tinytinyrss_file)]

- src\app\utils\run_services.py [L299]: cmd = base_compose + ["-f", str(opensearch_file), "up", "-d"]

- src\app\utils\run_services.py [L327]: config_cmd = compose_cmd + ["-f", str(cf), "config", "--services"]

- src\app\utils\run_services.py [L345]: check_cmd = ["docker", "ps", "-a", "--filter", f"label=com.docker.compose.service={svc}", "--format", "{{.Names}}"]

- src\app\utils\run_services.py [L359]: up_cmd = compose_cmd + ["-f", str(cf), "up", "-d"] + missing_services

- src\app\utils\run_services.py [L376]: cmd = compose_cmd + ["-f", str(cf), "up", "-d"]

- src\app\utils\run_services.py [L482]: cmd = ["ollama", "create", model_name, "-f", str(modelfile)]

- src\app\utils\run_services.py [L508]: logger.info(f"Container '{name}' already running.")

- src\app\utils\run_services.py [L517]: logger.success(f"Container '{name}' started successfully.")

- src\app\utils\run_services.py [L521]: f"Container '{name}' is not running and could not be started (attempt {attempts})."

- src\app\utils\run_services.py [L524]: logger.error(f"Container '{name}' could not be started after {attempts} attempts.")

- src\app\utils\run_services.py [L526]: logger.error(f"Unexpected error ensuring container '{name}': {e}")

- src\app\utils\run_services.py [L582]: logger.error(f"Error while ensuring Ollama/model: {e}")

- src\app\utils\run_services.py [L656]: cmd = compose_cmd + ["-f", str(cf), "down", "-v"]

- src\app\utils\run_services.py [L707]: ps_proc = subprocess.run(["wsl", "-d", distro_name, "--", "docker", "ps", "-q", "--filter", f"name={name}"], capture_output=True, text=True, check=False)

- src\app\utils\run_services.py [L710]: ps_proc = subprocess.run(["docker", "ps", "-q", "--filter", f"name={name}"], capture_output=True, text=True, check=False)

- src\app\utils\run_services.py [L714]: logger.info(f"No running containers found matching '{name}' to stop.")

- src\app\utils\run_services.py [L721]: logger.exception(f"Failed to stop container {cid} (target '{name}')")

- src\app\utils\run_services.py [L723]: logger.error(f"Error while attempting to stop target container '{name}': {e}")

- src\app\utils\run_services.py [L725]: logger.success(f"Requested stop for {stopped} target container(s).")

- src\app\utils\run_services.py [L729]: logger.error(f"Error while attempting to stop containers: {e}")

- src\app\utils\run_services.py [L741]: logger.warning(f"`ollama stop` failed: {e}; trying process kill fallback")

- src\app\utils\run_services.py [L748]: _run(["pkill", "-f", "ollama"]) if not (platform.system() == "Windows" and distro_name) else _run("pkill -f ollama", shell=True)

- src\app\utils\run_services.py [L751]: logger.error(f"Failed to kill Ollama processes: {e2}")

- src\app\utils\run_services.py [L757]: logger.error(f"Error during shutdown_services: {e}")

- src\app\utils\utils.py [L68]: result = (0, f'File \'{filename}\' read successfully.', content)

- src\app\utils\utils.py [L80]: result = (4, f'Unknown error: {e.__class__.__name__}.')

- src\app\utils\utils.py [L132]: result = (0, f'File \'{filename}\' written successfully.')

- src\app\utils\utils.py [L144]: result = (4, f'Unknown error: {e.__class__.__name__}.')

- src\app\utils\utils.py [L189]: result = (1, f'Error while reading the file: {other_return[1]}')

- src\app\utils\utils.py [L249]: result = (1, f'Error while reading the file: {other_return[1]}')

- src\app\utils\utils.py [L315]: result = (1, f'Error recreating the file: {other_return[1]}')

- src\app\utils\utils.py [L318]: result = (0, f'File \'{file_name}\' successfully recreated.')

- src\app\controllers\routes\llm_controller.py [L38]: logger.debug(f"[LLM Client] Sending response to the user.")

- src\app\controllers\routes\llm_controller.py [L62]: logger.error(f"[LLM Trainer] Error in 7-day loop: {e}")

- src\app\controllers\routes\llm_controller.py [L85]: return {"message": f"Worker {name} already running"}

- src\app\controllers\routes\llm_controller.py [L93]: logger.info(f"[LLM] Updater started via /llm/updater")

- src\app\controllers\routes\llm_controller.py [L124]: logger.info(f"[LLM] Updater stopped via /llm/stop-updater")

- src\app\controllers\routes\network_analysis_controller.py [L117]: raise HTTPException(status_code=504, detail=f"nmap scan timed out after {timeout_sec} seconds")

- src\app\controllers\routes\network_analysis_controller.py [L133]: raise HTTPException(status_code=500, detail=f"scan failed: {e}")

- src\app\controllers\routes\network_analysis_controller.py [L176]: raise HTTPException(status_code=400, detail=f"invalid IP/CIDR: {e}")

- src\app\controllers\routes\network_analysis_controller.py [L180]: raise HTTPException(status_code=400, detail=f"range too large ({len(hosts)} hosts). Max allowed is {max_allowed}")

- src\app\controllers\routes\network_analysis_controller.py [L210]: return {"host": host, "error": f"nmap timeout after {timeout_sec}s"}

- src\app\controllers\routes\scrapy_news_controller.py [L78]: detail=f"Error validating the feed: {e}"

- src\app\controllers\routes\scrapy_news_controller.py [L83]: f.write(f"{url} | {title}\n")

- src\app\controllers\routes\scrapy_news_controller.py [L145]: logger.error(f"Scraping failed: {e}")

- src\app\controllers\routes\scrapy_news_controller.py [L148]: detail=f"Scraping failed: {str(e)}"

- src\app\controllers\routes\scrapy_news_controller.py [L256]: logger.error(f"[Feeds] Error extracting feeds: {e}")

- src\app\controllers\routes\scrapy_news_controller.py [L274]: logger.error(f"[Scheduler] Error rescheduling Google Alerts: {e}")

- src\app\controllers\routes\scrapy_news_controller.py [L332]: logger.error(f"[Scraper] run_dork_search_feed raised: {exc}")

- src\app\controllers\routes\scrapy_news_controller.py [L336]: logger.error(f"[Scraper] Error inspecting future: {_e}")

- src\app\controllers\routes\scrapy_news_controller.py [L344]: logger.error(f"[Scraper] Error during Google Dorking tasks: {e}")

- src\app\controllers\routes\scrapy_news_controller.py [L360]: logger.error(f"[Scheduler] Error rescheduling scraping: {e}")

- src\app\controllers\routes\scrapy_news_controller.py [L413]: logger.error(f"[Scraper] run_news_search raised: {exc}")

- src\app\controllers\routes\scrapy_news_controller.py [L417]: logger.error(f"[Scraper] Error inspecting future: {_e}")

- src\app\controllers\routes\scrapy_news_controller.py [L424]: logger.error(f"[Scraper] Error during Google Dorking tasks: {e}")

- src\app\controllers\routes\scrapy_news_controller.py [L440]: logger.error(f"[Scheduler] Error rescheduling scraping: {e}")

- src\app\controllers\routes\spacy_controller.py [L91]: logger.error(f"[SpaCy] Error while labeling entities: {e}")

- src\app\controllers\routes\spacy_controller.py [L108]: logger.error(f"[Scheduler] Error scheduling next SpaCy run: {e}")

- src\app\controllers\routes\tiny_postgres_controller.py [L147]: logger.error(f"[RSS] Error during RSS extraction and saving: {e}")

- src\app\controllers\routes\tiny_postgres_controller.py [L158]: logger.error(f"[RSS] extract_rss_and_save raised: {exc}")

- src\app\controllers\routes\tiny_postgres_controller.py [L162]: logger.error(f"[RSS] Error inspecting future: {_e}")

- src\app\controllers\routes\tiny_postgres_controller.py [L169]: logger.error(f"[RSS] Error scheduling RSS extraction task: {e}")

- src\app\controllers\routes\tiny_postgres_controller.py [L186]: logger.error(f"[Scheduler] Error rescheduling RSS extraction: {e}")

- src\app\controllers\routes\tiny_postgres_controller.py [L237]: detail=f"Error retrieving feeds: {str(e)}"

- src\app\controllers\routes\worker_controller.py [L112]: logger.info(f"Worker {name} disabled via UI.")

- src\app\controllers\routes\worker_controller.py [L113]: return {"message": f"Worker {name} disabled"}

- src\app\controllers\routes\worker_controller.py [L178]: logger.info(f"Worker {name} enabled via UI.")

- src\app\controllers\routes\worker_controller.py [L179]: return {"message": f"Worker {name} enabled"}

- src\app\services\llm\finetune_dataset_builder.py [L23]: logger.warning(f"[FinetuneBuilder] File not found: {path}")

- src\app\services\llm\finetune_dataset_builder.py [L29]: logger.error(f"[FinetuneBuilder] Error loading {path}: {e}")

- src\app\services\llm\finetune_dataset_builder.py [L70]: logger.error(f"[FinetuneBuilder] Error processing CVE item: {e}")

- src\app\services\llm\finetune_dataset_builder.py [L88]: input_text = f"Título: {title}\n\nContenido:\n{body}"

- src\app\services\llm\finetune_dataset_builder.py [L106]: f"[FinetuneBuilder] Dataset built at {output_path} with {total_examples} examples."

- src\app\services\llm\llm_client.py [L30]: url = f"{OLLAMA_BASE_URL}/api/chat"

- src\app\services\llm\llm_client.py [L44]: logger.debug(f"[LLM Client] Sending request to Ollama model={OLLAMA_MODEL_NAME}")

- src\app\services\llm\llm_client.py [L65]: logger.error(f"[LLM Client] Error while querying Ollama: {e}")

- src\app\services\llm\script_auto.py [L36]: logger.info(f"Repository already exists at {repo_dir}, skipping clone.")

- src\app\services\llm\script_auto.py [L39]: logger.info(f"Cloning repository from {repo_url} into {repo_dir} ...")

- src\app\services\llm\script_auto.py [L65]: logger.error(f"Error while cloning repository: return {ret} stdout={out} stderr={err}")

- src\app\services\llm\script_auto.py [L71]: logger.error(f"Error while cloning repository: {e}")

- src\app\services\llm\script_auto.py [L74]: logger.error(f"Unexpected error cloning repository: {e}")

- src\app\services\llm\script_auto.py [L86]: logger.warning(f"Repository directory {repo_dir} does not exist. Cannot run git pull.")

- src\app\services\llm\script_auto.py [L89]: logger.info(f"Updating repository in {repo_dir} ...")

- src\app\services\llm\script_auto.py [L113]: logger.error(f"Error while updating repository: return {ret} stdout={out} stderr={err}")

- src\app\services\llm\script_auto.py [L119]: logger.error(f"Error while updating repository: {e}")

- src\app\services\llm\script_auto.py [L122]: logger.error(f"Unexpected error updating repository: {e}")

- src\app\services\llm\script_auto.py [L139]: logger.info(f"Stop event set before processing {file_path}; skipping.")

- src\app\services\llm\script_auto.py [L146]: logger.info(f"Stop event set while reading {file_path}; aborting.")

- src\app\services\llm\script_auto.py [L153]: logger.warning(f"{file_path} was not included (CVE not published or error).")

- src\app\services\llm\script_auto.py [L157]: logger.info(f"Stop event set before appending {file_path}; aborting append.")

- src\app\services\llm\script_auto.py [L162]: logger.warning(f"Warning: {file_path} is not valid JSON. Skipping.")

- src\app\services\llm\script_auto.py [L164]: logger.error(f"Error processing {file_path}: {e}")

- src\app\services\llm\script_auto.py [L217]: logger.info(f"Processing {total_files} JSON files...")

- src\app\services\llm\script_auto.py [L237]: out_path = os.path.join(tempdir, f"out_{i}.json")

- src\app\services\llm\script_auto.py [L287]: logger.warning(f"Failed reading partial output {out}")

- src\app\services\llm\script_auto.py [L308]: logger.info(f"\nConsolidation completed. Processed {total_files} JSON files.")

- src\app\services\llm\script_auto.py [L309]: logger.info(f"Output file saved as: {output_file}")

- src\app\services\llm\script_auto.py [L311]: logger.error(f"Error during consolidation: {e}")

- src\app\services\llm\script_auto.py [L465]: input_text = f"""

- src\app\services\llm\script_auto.py [L501]: output_text = f"""

- src\app\services\llm\script_auto.py [L525]: "instruction": f"Describe in a structured way the vulnerability {cve_id}",

- src\app\services\llm\script_auto.py [L532]: logger.error(f"Error transforming CVE: {e}")

- src\app\services\scraping\feeds_gd.py [L70]: logger.info(f"🔎 Searching with dork: {dork}")

- src\app\services\scraping\feeds_gd.py [L79]: logger.success(f"Found URL: {url}")

- src\app\services\scraping\feeds_gd.py [L88]: logger.error(f"Error while searching with dork '{dork}': {e}")

- src\app\services\scraping\feeds_gd.py [L93]: logger.info(f"Waiting {sleep_time:.2f} seconds before next search...")

- src\app\services\scraping\google_alerts_pages.py [L61]: logger.error(f"Feeds file not found: {FEEDS_FILE_PATH}")

- src\app\services\scraping\google_alerts_pages.py [L79]: logger.info(f"Reading feed: {feed_url}")

- src\app\services\scraping\google_alerts_pages.py [L83]: logger.warning(f"No entries found in: {feed_url}")

- src\app\services\scraping\google_alerts_pages.py [L123]: logger.info(f"{len(new_urls)} new URLs saved to {URLS_FILE_PATH}")

- src\app\services\scraping\news_gd.py [L90]: logger.warning(f"Error processing {url}: {e}")

- src\app\services\scraping\news_gd.py [L150]: logger.error(f"Failed to append news item: {e}")

- src\app\services\scraping\news_gd.py [L167]: logger.info(f"Searching with dork: {dork}")

- src\app\services\scraping\news_gd.py [L178]: logger.success(f"Added news from {url}")

- src\app\services\scraping\news_gd.py [L183]: logger.error(f"rror during search with dork '{dork}': {e}")

- src\app\services\scraping\news_gd.py [L186]: logger.info(f"Waiting {sleep_time} seconds before next dork...")

- src\app\services\scraping\spider_factory.py [L131]: elements = response.css(f"{tag}::text").getall()

- src\app\services\scraping\spider_factory.py [L140]: logger.info(f"URL relacionada con ciberseguridad: {response.url}")

- src\app\services\scraping\spider_factory.py [L143]: logger.info(f"Descartada (no relevante): {response.url}")

- src\app\services\scraping\spider_factory.py [L144]: logger.info(f"URL: {response.url} scrapeada")

- src\app\services\scraping\spider_factory.py [L238]: logger.warning(f"DB pool not available; will retry later: {e}")

- src\app\services\scraping\spider_factory.py [L254]: logger.info(f"Scraped lap {number}: {len(urls)} URLs to process")

- src\app\services\scraping\spider_factory.py [L266]: f'{parameters[0]};{parameters[1]}\n'

- src\app\services\scraping\spider_factory.py [L311]: logger.exception(f"Error acquiring DB connection from pool or processing URLs: {e}")

- src\app\services\scraping\spider_rss.py [L57]: logger.error(f"Error reading file: {e}")

- src\app\services\scraping\spider_rss.py [L85]: href = link.attrib.get("href", "")

- src\app\services\scraping\spider_rss.py [L91]: logger.info(f"RSS found: {full_url}")

- src\app\services\scraping\spider_rss.py [L179]: logger.warning(f"⚠️  No entries found in {feed_url}")

- src\app\services\scraping\spider_rss.py [L194]: logger.info(f"✅ Feed inserted: {feed_url}")

- src\app\services\scraping\spider_rss.py [L197]: logger.error(f"❌ Error processing {feed_url}: {e}")

- src\app\services\spacy\text_processor.py [L44]: logger.warning(f"Could not load spaCy model '{pkg}' for lang '{lang_code}': {e}. Falling back to 'es' model.")

- src\app\services\spacy\text_processor.py [L51]: logger.error(f"Failed loading fallback spaCy model 'es_core_news_sm': {e2}")

- src\app\services\spacy\text_processor.py [L121]: f'{parameters[0]};{parameters[1]}\n'

- src\app\services\spacy\text_processor.py [L157]: logger.info(f"Text already indexed, skipping: {text[:80]}...")

- tests\test_run_services_ollama.py [L107]: assert found, f"Expected ollama create to be called; calls: {calls}"

- tests\utils\test_run_services_combined.py [L70]: self.assertTrue(matched, f"Expected combined compose invocation, got calls: {str_calls}")

- tests\utils\test_run_services_combined.py [L71]: self.assertTrue(any('Install' in c and 'stack.env' in c for c in matched), f"Expected env-file in Install/, matched calls: {matched}")

- tests\utils\test_run_services_combined.py [L89]: self.assertTrue(any(call and call[0] == 'sudo' for call in list_calls), f"Expected sudo prefix in commands, got: {list_calls}")
