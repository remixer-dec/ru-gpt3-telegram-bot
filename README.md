### RU-GPT3 Telegram bot  
This is a simple bot for [ru-GPT3](https://github.com/sberbank-ai/ru-gpts "Russian GPT-3") model. It has a few commands to interact with the model and a dialog/chat mode.  
  
Configuration is stored in config.json file. First 7 configuration options are described in the original model repo.  
  
Extra options:  
tg_token - telegram bot token  
role - AI personality biography  
rod - word ending parameter [m/j/s]  
admin_id - bot administrator ID  
history [chat / user] *With user-based history, the dialog is formed only on the messages with every user separately, otherwise, on all messages in group chat that are visible to the bot.*  
  
#### Usage:  
```pip install -r requirements.txt ```  
```python ruGPTtgBot.py```  
  
#### Links:
[More about GPT-3](https://www.youtube.com/watch?v=SY5PvZrJhLE)  
[More about interactions with GPT-like models](https://www.youtube.com/watch?v=t86G11tfVNw)  
P.S. I created this bot before watching this^ video. 

