import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncGenerator

from app.core.logging import get_logger
from app.llm.models.base import BaseLLMModel
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class MLXModel(BaseLLMModel):
    """MLX-based LLM implementation optimized for Apple Silicon"""
    
    def __init__(self, model_name: str, model_path: Optional[str] = None):
        """
        Initialize the MLX model.
        
        Args:
            model_name: A name identifier for the model
            model_path: Path to the model or HF repo id (default: use model_name)
        """
        self._model_name = model_name
        self._model_path = model_path or model_name
        self._loaded = False
        self._model = None
        self._tokenizer = None
    
    async def load(self) -> Dict[str, Any]:
        """
        Load the model using mlx_lm.
        
        Returns:
            Dict with load status information
        """
        logger.info(f"Loading MLX model: {self._model_path}")
        
        start_time = time.time()
        
        # Use asyncio.to_thread to run sync mlx_lm load in a separate thread
        def _load_model():
            try:
                # Import here to avoid loading MLX modules when not needed
                from mlx_lm import load
                model, tokenizer = load(self._model_path)
                return model, tokenizer
            except Exception as e:
                logger.error(f"Error loading MLX model: {str(e)}")
                raise
        
        try:
            self._model, self._tokenizer = await asyncio.to_thread(_load_model)
            self._loaded = True
            load_time = time.time() - start_time
            
            logger.info(f"Successfully loaded MLX model in {load_time:.2f} seconds")
            return {
                "name": self._model_name,
                "path": self._model_path,
                "loaded": True,
                "load_time_seconds": load_time
            }
        except Exception as e:
            logger.error(f"Failed to load MLX model: {str(e)}")
            return {
                "name": self._model_name,
                "path": self._model_path,
                "loaded": False,
                "error": str(e)
            }
    
    async def generate(self, prompt: str, params: Optional[Dict] = None) -> str:
        """
        Generate text using the MLX model.
        
        Args:
            prompt: Input text prompt
            params: Generation parameters
            
        Returns:
            Generated text response
        """
        if not self._loaded:
            await self.load()
        
        params = params or {}
        
        async def _generate():
            try:
                # Import generate function inside the thread
                from mlx_lm import generate
                
                # Prepare the prompt with chat template if available
                processed_prompt = prompt
                if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template is not None:
                    messages = [{"role": "user", "content": prompt}]
                    processed_prompt = self._tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                
                # Set generation parameters
                gen_params = {
                    "max_tokens": params.get("max_tokens", 512),
                    #"temperature": params.get("temperature", 0.7),
                    #"top_p": params.get("top_p", 0.9),
                    #"verbose": params.get("verbose", False)
                }
                
                # Generate response
                response = generate(
                    self._model, 
                    self._tokenizer, 
                    prompt=processed_prompt, 
                    **gen_params
                )
                
                return response
            except Exception as e:
                logger.error(f"Error generating text with MLX: {str(e)}")
                raise
        
        logger.info(f"Generating text with MLX model {self._model_name}")
        return await asyncio.to_thread(_generate)
    
    async def chat(self, messages: List[Dict], params: Optional[Dict] = None) -> Dict:
        """
        Generate a chat completion using the MLX model.
        
        Args:
            messages: List of chat messages in the format [{"role": "...", "content": "..."}]
            params: Generation parameters
            
        Returns:
            Chat completion response
        """
        if not self._loaded:
            await self.load()
        
        params = params or {}
        
        async def _chat():
            try:
                # Import generate function inside the thread
                from mlx_lm import generate
                
                # Apply chat template if available
                if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template is not None:
                    processed_prompt = self._tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                else:
                    # Fallback for models without chat template
                    processed_prompt = self._format_messages(messages)
                
                # Set generation parameters
                gen_params = {
                    "max_tokens": params.get("max_tokens", 512),
                    #"temp": params.get("temperature", 0.7),
                    #"top_p": params.get("top_p", 0.9),
                    #"verbose": params.get("verbose", False)
                }
                
                # Generate response
                response_text = generate(
                    self._model, 
                    self._tokenizer, 
                    prompt=processed_prompt, 
                    **gen_params
                )
                
                # Format response as chat completion API format
                return {
                    "id": f"mlx-{int(time.time())}",
                    "model": self._model_name,
                    "created": int(time.time()),
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"Error in chat completion with MLX: {str(e)}")
                raise
        
        logger.info(f"Generating chat completion with MLX model {self._model_name}")
        return await asyncio.to_thread(_chat)

    #async def chat_stream(self, messages: List[Dict], params: Optional[Dict] = None) -> AsyncGenerator[Dict, None]:
    #"""
    #Stream a chat completion response using the MLX model.
    #
    #Args:
    #    messages: List of chat messages in the format [{"role": "...", "content": "..."}]
    #    params: Generation parameters
    #    
    #Yields:
    #    Response chunks in streaming format
    #"""
    #if not self._loaded:
    #    await self.load()
    #
    #params = params or {}
    #
    #async def _chat_stream():
    #    try:
    #        # Import necessary functions inside the thread
    #        from mlx_lm import generate
    #        
    #        # Apply chat template if available
    #        if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template is not None:
    #            processed_prompt = self._tokenizer.apply_chat_template(
    #                messages, tokenize=False, add_generation_prompt=True
    #            )
    #        else:
    #            # Fallback for models without chat template
    #            processed_prompt = self._format_messages(messages)
    #        
    #        # Set generation parameters
    #        gen_params = {
    #            "max_tokens": params.get("max_tokens", 512),
    #            "stream": True  # Ensure streaming is enabled
    #        }
    #        
    #        # Create a unique ID for this streaming session
    #        stream_id = f"chatcmpl-{int(time.time())}"
    #        
    #        # Generate initial response with empty content
    #        initial_chunk = {
    #            "id": stream_id,
    #            "object": "chat.completion.chunk",
    #            "created": int(time.time()),
    #            "model": self._model_name,
    #            "choices": [
    #                {
    #                    "index": 0,
    #                    "delta": {"role": "assistant"},
    #                    "finish_reason": None
    #                }
    #            ]
    #        }
    #        
    #        # Use a Queue to communicate between threads
    #        queue = asyncio.Queue()
    #        
    #        # Put the initial chunk in the queue
    #        await queue.put(initial_chunk)
    #        
    #        def _token_callback(token):
    #            # This function is called for each token generated
    #            chunk = {
    #                "id": stream_id,
    #                "object": "chat.completion.chunk",
    #                "created": int(time.time()),
    #                "model": self._model_name,
    #                "choices": [
    #                    {
    #                        "index": 0,
    #                        "delta": {"content": token},
    #                        "finish_reason": None
    #                    }
    #                ]
    ##            }
    #            
    #            # Use asyncio.run_coroutine_threadsafe to add chunk to queue from callback
    #            asyncio.run_coroutine_threadsafe(
    #                queue.put(chunk), 
    #                asyncio.get_event_loop()
    #            )
    #        
    #        def _generate_with_callback():
    #            # Modified generate function that calls the callback for each token
    #            # Initialize tokenizer and model
    #            tokenizer = self._tokenizer
    #            model = self._model
    #            
    #            # Tokenize the prompt
    #            tokens = tokenizer.encode(processed_prompt)
    #            
    #            # Generate tokens one by one
    #            for i in range(gen_params["max_tokens"]):
    #                next_token = model.generate(tokens, temp=params.get("temperature", 0.7))
    #                if next_token == tokenizer.eos_token_id:
    #                    break
    #                
    #                # Decode the single token and call the callback
    #                token_text = tokenizer.decode([next_token])
    #                _token_callback(token_text)
    #                
    #                # Append token to sequence for next iteration
    #                tokens.append(next_token)
    #            
    #            # Signal completion
    #            final_chunk = {
    #                "id": stream_id,
    #                "object": "chat.completion.chunk",
    #                "created": int(time.time()),
    #                "model": self._model_name,
    #                "choices": [
    #                    {
    #                        "index": 0,
    #                        "delta": {},
    #                        "finish_reason": "stop"
    #                    }
    #                ]
    #            }
    #            
    #            asyncio.run_coroutine_threadsafe(
    #                queue.put(final_chunk), 
    #                asyncio.get_event_loop()
    #            )
    #            
    #            # Mark queue as done
    #            asyncio.run_coroutine_threadsafe(
    #                queue.put(None),  # None signals end of stream
    #                asyncio.get_event_loop()
    #            )
    #        
    #        # Start generation in a separate thread
    #        loop = asyncio.get_event_loop()
    #        await loop.run_in_executor(None, _generate_with_callback)
    #        
    #        # Yield chunks from the queue
    #        while True:
    #            chunk = await queue.get()
    #            if chunk is None:  # End of stream
    #                break
    #            yield chunk
    #            
    #    except Exception as e:
    #        logger.error(f"Error in chat streaming with MLX: {str(e)}")
    #        # Yield an error message
    #        error_chunk = {
    #            "object": "chat.completion.chunk",
    #            "error": {
    #                "message": str(e),
    #                "type": "server_error"
    #            }
    #        }
    #        yield error_chunk
    #
    #logger.info(f"Streaming chat completion with MLX model {self._model_name}")
    #async for chunk in _chat_stream():
    #    yield chunk



    async def chat_stream(self, messages: List[Dict], params: Optional[Dict] = None) -> AsyncGenerator[Dict, None]:
        """
        Stream a chat completion response using the MLX model.
        
        Args:
            messages: List of chat messages in the format [{"role": "...", "content": "..."}]
            params: Generation parameters
            
        Yields:
            Response chunks in streaming format
        """
        if not self._loaded:
            await self.load()
        
        params = params or {}
        
        # Create a unique ID for this streaming session
        stream_id = f"chatcmpl-{int(time.time())}"
        
        # First, yield the initial role chunk
        yield {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self._model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None
                }
            ]
        }
        
        try:
            # Process the messages into a prompt
            if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template is not None:
                processed_prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            else:
                processed_prompt = self._format_messages(messages)
            
            # Encode the prompt
            encoded_prompt = self._tokenizer.encode(processed_prompt)
            
            # Set generation parameters
            max_tokens = params.get("max_tokens", 512)
            temperature = params.get("temperature", 0.7)
            top_p = params.get("top_p", 0.9)
            
            # Define a function that uses mlx_lm.stream_generate to generate and stream tokens
            def generate_streaming():
                # Import stream_generate inside the thread to avoid loading MLX modules when not needed
                from mlx_lm import stream_generate
                
                
                # Use the stream_generate function from mlx_lm
                generator = stream_generate(
                    model=self._model,
                    tokenizer=self._tokenizer,
                    prompt=encoded_prompt,
                    max_tokens=max_tokens,
                )
                
                return generator
            
            # Run the generation in a separate thread
            loop = asyncio.get_event_loop()
            generator = await loop.run_in_executor(None, generate_streaming)
            
            # Process and yield chunks as they are generated
            for response in generator:
                if response.text:
                    yield {
                        "id": stream_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": self._model_name,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": response.text},
                                "finish_reason": None
                            }
                        ]
                    }
            
            # Yield the final chunk to signal completion
            yield {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": self._model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in chat streaming with MLX: {str(e)}")
            yield {
                "object": "chat.completion.chunk",
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }




    def _make_sampler(temp=0.7, top_p=0.9, min_p=0.0, min_tokens_to_keep=1):
        """
        Create a sampler function for token generation.
        
        Args:
            temp: Temperature for sampling
            top_p: Top-p (nucleus) sampling parameter
            min_p: Min-p sampling parameter
            min_tokens_to_keep: Minimum tokens to keep for min-p sampling
            
        Returns:
            A sampler function that takes logits and returns token indices
        """
        def sample(logits):
            import mlx.core as mx
            from mlx.utils import sample_logits
            
            if temp == 0:
                # Greedy sampling
                return mx.argmax(logits, axis=-1)
            else:
                # Use sample_logits for non-greedy sampling
                return sample_logits(
                    logits, 
                    temp=temp, 
                    top_p=top_p,
                    min_p=min_p,
                    min_tokens_to_keep=min_tokens_to_keep
                )
        
        return sample


    
    def _format_messages(self, messages: List[Dict]) -> str:
        """
        Format chat messages into a single prompt for models without chat templates.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt string
        """
        formatted_prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"
        
        formatted_prompt += "Assistant: "
        return formatted_prompt
    
    def unload(self) -> bool:
        """
        Unload the model from memory.
        
        Returns:
            True if successful, False otherwise
        """
        was_loaded = self._loaded
        self._model = None
        self._tokenizer = None
        self._loaded = False
        
        if was_loaded:
            logger.info(f"Unloaded MLX model: {self._model_name}")
        
        return was_loaded
    
    @property
    def name(self) -> str:
        return self._model_name
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
