# Local language models for a 16 GB card with long context

Checked October 18, 2026 against the model cards and docs linked below. Speeds and "fits" figures that come from third-party blogs are marked as such. Anything marked **computed** is my arithmetic from the published `config.json`. Nothing here has been run on your card yet; `coproducer probe models` and Gate 0 measure it.

## Current default (measured on the target machine)

The brain that Gate 0 measured and that `config.toml` now uses is **`gemma4:12b`, served by Ollama** (`[llm] model`). The exact version of Ollama and of every model is recorded in `docs/DEPENDENCIES.md` (generated from `src/coproducer/data/deps.lock.json`). Pull it with `ollama pull gemma4:12b`; `coproducer deps` checks the pulled model is present. The Qwen3.5-9B research below is the original pre-measurement recommendation and is kept for its VRAM arithmetic and as the fallback; it is not the default.

## Original recommendation (before measurement)

One resident model for all three jobs (agent brain, task-card coder, GUI grounding): **Qwen3.5-9B**, Q4_K_M or UD-Q4_K_XL, served by Ollama.

| Reason | Evidence |
| --- | --- |
| Long context is cheap on this architecture | 3 of every 4 layers are linear attention (Gated DeltaNet); only 8 of 32 layers keep a KV cache, with 4 KV heads of dimension 256 ([config.json](https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/config.json)). **Computed:** 32 KiB per token at f16, so 128K tokens is 4.0 GiB, 262K is 8.0 GiB; at `q8_0` cache, 2.1 GiB and 4.3 GiB |
| Native 262,144 token context, Apache-2.0, accepts images | [Model card](https://huggingface.co/Qwen/Qwen3.5-9B), [Ollama tags](https://ollama.com/library/qwen3.5) (all tags: 256K, text and image) |
| Best tool-use numbers in its size class (vendor reported) | BFCL-V4 66.1 and TAU2-Bench 79.1, versus 49.7 and 57.4 for Qwen3-Next-80B-A3B-Thinking, same table ([model card](https://huggingface.co/Qwen/Qwen3.5-9B)) |
| Screen grounding is credible | ScreenSpot Pro 65.2, OSWorld-Verified 41.8 (vendor reported, same card). It is not benchmarked on FL Studio, so Gate 0 checks it |
| Small enough to leave room for the audio models | Q4_K_M is 5.68 GB, UD-Q4_K_XL 5.97 GB, Q8_0 9.53 GB ([Unsloth GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)) |

## Memory budget on 16 GB (computed, then measured at Gate 0)

| Setup | Weights | KV cache | Total before runtime overhead |
| --- | --- | --- | --- |
| Q4_K_M, 128K context, `q8_0` cache | 5.7 GB | 2.1 GiB | about 7.8 |
| Q4_K_M, 262K context, `q8_0` cache | 5.7 GB | 4.3 GiB | about 10.0 |
| Q8_0, 128K context, `q8_0` cache | 9.5 GB | 2.1 GiB | about 11.6 |

The model card advises keeping at least 128K of context to preserve thinking quality, so 128K is the default. A third-party guide notes that recall degrades past roughly 100K to 200K tokens ([InsiderLLM](https://insiderllm.com/guides/qwen-3-5-9b-setup-guide/)), so a bigger window is not always better.

## The catch: the audio models share the card

ACE-Step 1.5 recommends a 2B turbo model with a 0.6B or 1.7B planner for 8 to 16 GB cards, and runs in 6 GB or less with offload ([README](https://github.com/ACE-Step/ACE-Step-1.5)). Demucs needs at least 3 GB. With the brain resident at 8 to 10 GB, generation is tight and Music Flamingo (8B) does not fit beside it. The scheduler already refuses a load that does not fit (`E_GPU_BUDGET`). Three ways to live with it, in order of preference:

1. Keep the brain at 64K to 128K with `q8_0` cache and run ACE-Step in its smallest tier (`turbo+lm0.6B`, already the default variant).
2. Unload the brain while a heavy audio model runs: `ollama stop qwen3.5:9b`, or send `keep_alive: 0` ([Ollama FAQ](https://docs.ollama.com/faq)). Reload is a few seconds.
3. Use Qwen3.5-4B (3.3 to 4.0 GB download) as the brain. Its reported TAU2-Bench is 79.9 and BFCL-V4 50.3, but it has less headroom for hard coding.

## Server settings (Ollama)

Per the [Ollama FAQ](https://docs.ollama.com/faq): default context is 4096 tokens, so set it explicitly or the long window is never used.

```
OLLAMA_CONTEXT_LENGTH=131072
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_KEEP_ALIVE=30m
ollama pull qwen3.5:9b
```

`coproducer` defaults now point at `http://127.0.0.1:11434/v1` with model `qwen3.5:9b` (`[llm]` in `config.toml`). Use the sampling settings on the model card; thinking mode is on by default and the model card shows how to turn it off for fast tool calls.

## Per-job notes

| Job | Model | Note |
| --- | --- | --- |
| Agent brain | Qwen3.5-9B | Thinking on for planning, off for routine tool calls. Keep only final answers in history ([Unsloth card](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)) |
| Task-card coder | Qwen3.5-9B | LiveCodeBench v6 65.6 on the model card, against 74.6 for gpt-oss-20b. The card loop's gate (real pytest in a scratch copy) catches weak output, and cards are tiny by design |
| GUI grounding | Qwen3.5-9B first | Confirmed for image input through Ollama. llama.cpp's multimodal page does not list Qwen3.5 or Qwen3-VL, so do not plan on llama-server for images ([llama.cpp docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)). Fallback if it misses FL buttons: Qwen3-VL 8B, about 6 GB at Q4 ([InsiderLLM](https://insiderllm.com/guides/vision-models-locally/)) |

## Alternatives considered

| Model | Why it is not the default |
| --- | --- |
| gpt-oss-20b (MXFP4, fits 16 GB, Apache-2.0, function calling: [card](https://huggingface.co/openai/gpt-oss-20b)) | Stronger on LiveCodeBench (74.6) but a 12.1 GB file leaves about 2 GB for cache, so long context is not realistic. One third-party test saw speed fall to about 9 tok/s at a 128K setting ([RunAIHome](https://www.runaihome.com/blog/best-local-llm-16gb-vram-2026/)). Good swap-in for hard coding at short context |
| Devstral Small 2 24B | Third-party figures put it above 16 GB at 8K unless the cache is quantized, so no long context ([RunAIHome](https://www.runaihome.com/blog/best-local-llm-16gb-vram-2026/)) |
| Qwen3.5-27B | About 17 to 20 GB download ([Ollama](https://ollama.com/library/qwen3.5)). Does not fit |
| Ministral 3 14B, Granite 4.2 8B | Fit, with 256K and 128K context, but the reported tool-use numbers are lower or not given ([VDF](https://vdf.ai/blog/best-local-llm-for-agents-tool-calling/)) |

## Still to confirm on your machine

1. Real VRAM with the brain at 128K, plus ACE-Step turbo+lm0.6B beside it (`coproducer probe models`).
2. Tool-call reliability through Ollama's OpenAI-compatible endpoint across a 30-step plan.
3. Whether Qwen3.5-9B finds FL Studio controls from screenshots. Run it on your calibration screenshots before trusting it.
4. That Ollama still ships `qwen3.5:9b` with the same tag when you pull it.
