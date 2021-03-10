#!/usr/bin/env python3
# coding=utf-8
# Copyright 2018 Google AI, Google Brain and Carnegie Mellon University Authors and the HuggingFace Inc. team.
# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import torch
from transformers import (GPT2LMHeadModel, GPT2Tokenizer)
from configLoader import cfg
from datetime import datetime
from tgbot import bot, queue, history
from utils import *
import _thread

device = torch.device("cuda" if torch.cuda.is_available() and not cfg.no_cuda else "cpu")

model_type = 'gpt2'
model_class, tokenizer_class = GPT2LMHeadModel, GPT2Tokenizer
tokenizer = tokenizer_class.from_pretrained(cfg.model_name_or_path)


def set_seed(seed=datetime.now().microsecond):
    np.random.seed(seed)
    torch.manual_seed(seed)
    print("random seed is " + str(seed))
    if not cfg.no_cuda and torch.cuda.device_count() > 0:
        torch.cuda.manual_seed_all(seed)


set_seed(cfg.seed if hasattr(cfg, 'seed') else set_seed.__defaults__[0])

print("loading model data")
model = model_class.from_pretrained(cfg.model_name_or_path)
model.to(device)
print("model data loaded")


async def gpt_runtime():
    prompt_text = ""
    user = -1
    queue.activate(GPT_EVENT_LOOP)
    print("starting the bot")
    _thread.start_new_thread(bot.run, ())
    while not (prompt_text == cfg.stop_command and user == cfg.admin_id):
        prompt_text = ""
        while not len(prompt_text):
            prompt_text, reply, action, user, chat, loop, rparser, pmod = await queue.get_item()
        asyncio.run_coroutine_threadsafe(action('typing'), loop)
        asyncio.run_coroutine_threadsafe(delay(action, 5, 'typing'), loop)
        print('< ' + prompt_text)

        # Different models need different input formatting and/or extra arguments
        encoded_prompt = tokenizer.encode(prompt_text,
                                          add_special_tokens=False,
                                          return_tensors="pt")
        encoded_prompt = encoded_prompt.to(device)

        output_sequences = model.generate(
            input_ids=encoded_prompt,
            max_length=cfg.length + len(encoded_prompt[0]),
            temperature=cfg.temperature,
            top_k=cfg.kvalue,
            top_p=cfg.pvalue + pmod,
            repetition_penalty=cfg.repetition_penalty,
            do_sample=True,
            num_return_sequences=1,
        )

        # Remove the batch dimension when returning multiple sequences
        if len(output_sequences.shape) > 2:
            output_sequences.squeeze_()

        for generated_sequence_idx, generated_sequence in enumerate(
                output_sequences):
            generated_sequence = generated_sequence.tolist()
            text = tokenizer.decode(generated_sequence,
                                    clean_up_tokenization_spaces=True)

            # Remove all text after the stop token
            text = text[:text.find(cfg.stop_token) if cfg.stop_token else None]

            total_sequence = (
                #prompt_text +
                text[len(
                    tokenizer.decode(encoded_prompt[0],
                                     clean_up_tokenization_spaces=True)):].
                rsplit(' ', 1)[0])

            total_sequence = cut_extra_stuff(total_sequence)
            if rparser:
                if rparser != historic_response_parser:
                    total_sequence = rparser(total_sequence)
                else:
                    total_sequence = rparser(
                        total_sequence,
                        user if cfg.history == "user" else chat, history)

            print("> " + total_sequence)
            
            try:
                queue.limits[user] -= 1
                asyncio.run_coroutine_threadsafe(reply(total_sequence), loop)
            except Exception as e:
                print(str(e))


if __name__ == "__main__":
    GPT_EVENT_LOOP = asyncio.new_event_loop()
    GPT_EVENT_LOOP.run_until_complete(gpt_runtime())
