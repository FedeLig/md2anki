python -m llama_cpp.server \
  --model ./models/qwen2-vl-7b-instruct-q4_k_m.gguf \
  --clip_model_path ./models/mmproj-qwen2-vl-7b-instruct-f16.gguf \
  --chat_format chatml \
  --n_ctx 4096 \
  --port 8000