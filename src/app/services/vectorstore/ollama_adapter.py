"""
@file ollama_adapter.py
@author naflashDev
@brief Ollama-based embedding adapter.
@details Provides an embedding adapter that calls the local `ollama` CLI to obtain
embedding vectors from a model already installed in Ollama. Designed to be a
drop-in replacement for `EmbeddingAdapter` used by `ChromaClient`.
"""
import shutil
import subprocess
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class OllamaEmbeddingAdapter:
    """Adapter that uses the `ollama` CLI `run` command to request embeddings.

    It calls `ollama run <model> --format json` and expects the model to return
    an object containing an `embedding` array or raw numeric list depending on
    the model. This implementation is conservative and normalizes common shapes.
    """
    def __init__(self, model_name: str = "cybersentinel", dimensions: int = 1536):
        if not shutil.which('ollama'):
            raise RuntimeError('ollama CLI not found in PATH')
        self.model_name = model_name
        self.dimensions = dimensions

    def _call_ollama_run(self, prompt: str) -> object:
        # Use --format json and pass prompt as argument; capture stdout
        cmd = ['ollama', 'run', self.model_name, prompt, '--format', 'json']
        # Capture bytes and decode explicitly with utf-8 replacing invalid sequences
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode != 0:
            # decode stderr safely for logging
            try:
                serr = proc.stderr.decode('utf-8', errors='replace') if proc.stderr is not None else ''
            except Exception:
                serr = str(proc.stderr)
            raise RuntimeError(f"ollama run failed: {serr.strip()}")
        stdout_bytes = proc.stdout or b''
        try:
            stdout_text = stdout_bytes.decode('utf-8', errors='replace')
        except Exception:
            # fallback to latin1 to avoid breaking
            stdout_text = stdout_bytes.decode('latin1', errors='replace')
        try:
            return json.loads(stdout_text)
        except Exception:
            # If output is not JSON, return decoded stdout for downstream parsing/logging
            logger.debug('ollama output not JSON or parse failed; raw output: %s', stdout_text)
            return stdout_text

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        results = []
        # Attempt batching by joining with a separator if Ollama model handles multi prompts.
        # Safe fallback: call one-by-one.
        CHUNK_SIZE = 3000

        def _split_into_chunks(s: str, max_chars: int):
            words = s.split()
            chunks = []
            cur = []
            cur_len = 0
            for w in words:
                wl = len(w) + 1
                if cur_len + wl > max_chars and cur:
                    chunks.append(' '.join(cur))
                    cur = [w]
                    cur_len = len(w)
                else:
                    cur.append(w)
                    cur_len += wl
            if cur:
                chunks.append(' '.join(cur))
            # If splitting by words produced no chunks (e.g., very long token), fallback to fixed slices
            if not chunks and s:
                for i in range(0, len(s), max_chars):
                    chunks.append(s[i:i+max_chars])
            return chunks

        def _parse_embedding(out_obj):
            # Normalize likely shapes: {embedding: [...]} or [ ... ] or {embeddings: [...]}
            if isinstance(out_obj, dict):
                if 'embedding' in out_obj and isinstance(out_obj['embedding'], list):
                    return out_obj['embedding']
                if 'embeddings' in out_obj and isinstance(out_obj['embeddings'], list) and out_obj['embeddings']:
                    return out_obj['embeddings'][0]
                for v in out_obj.values():
                    if isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v):
                        return v
            elif isinstance(out_obj, list) and out_obj and all(isinstance(x, (int, float)) for x in out_obj):
                return out_obj
            return None

        for t in texts:
            # Sanitize input: Ollama / underlying CLI may fail on embedded null bytes
            if t is None:
                t_clean = ""
            else:
                t_clean = str(t)
            if "\x00" in t_clean:
                logger.warning('Input contains null character; removing before Ollama call')
                t_clean = t_clean.replace("\x00", "")
            # If the input is very long, split into chunks to avoid Windows command-line length limits
            chunks = [t_clean]
            if len(t_clean) > CHUNK_SIZE:
                chunks = _split_into_chunks(t_clean, CHUNK_SIZE)

            chunk_embeddings = []
            for chunk in chunks:
                try:
                    out = self._call_ollama_run(chunk)
                except Exception as e:
                    raise RuntimeError(f'Ollama embedding call failed: {e}')

                emb = _parse_embedding(out)

                if emb is None:
                    # If parsing failed, and we have raw text output, dump it for inspection
                    try:
                        if isinstance(out, str):
                            dump_dir = Path('data') / 'ollama_raw'
                            dump_dir.mkdir(parents=True, exist_ok=True)
                            h = hashlib.sha256(out.encode('utf-8') if isinstance(out, str) else b'').hexdigest()[:8]
                            fname = f"ollama_raw_{h}_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.txt"
                            dump_path = dump_dir / fname
                            with open(dump_path, 'w', encoding='utf-8') as df:
                                df.write(out)
                            logger.error('Could not parse embedding from ollama output; raw output dumped to %s', str(dump_path.as_posix()))
                    except Exception:
                        logger.exception('Failed to write raw ollama output for debugging')
                    raise RuntimeError('Could not parse embedding from ollama output')

                chunk_embeddings.append([float(x) for x in emb])
            

            # If multiple chunk embeddings, average them element-wise to produce a single embedding
            if not chunk_embeddings:
                raise RuntimeError('No embeddings returned from Ollama')
            if len(chunk_embeddings) == 1:
                emb_final = chunk_embeddings[0]
            else:
                # ensure consistent dimensions by truncating/padding with zeros
                max_len = max(len(e) for e in chunk_embeddings)
                norm = []
                for e in chunk_embeddings:
                    if len(e) < max_len:
                        e = e + [0.0] * (max_len - len(e))
                    elif len(e) > max_len:
                        e = e[:max_len]
                    norm.append(e)
                emb_final = [sum(vals) / len(norm) for vals in zip(*norm)]

            if self.dimensions and len(emb_final) != self.dimensions:
                logger.debug('Embedding length %s differs from expected %s', len(emb_final), self.dimensions)

            results.append([float(x) for x in emb_final])

        return results
