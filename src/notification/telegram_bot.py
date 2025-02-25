#!/usr/bin/env python3

import requests
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    """Třída pro odesílání zpráv přes Telegram."""
    
    def __init__(self, token, chat_id):
        """
        Inicializuje Telegram bota.
        
        Args:
            token (str): Token Telegram bota
            chat_id (str): ID chatu nebo kanálu
        """
        self.token = token
        self.chat_id = chat_id
    
    def send_message(self, text):
        """
        Odešle zprávu do Telegram chatu/kanálu.
        
        Args:
            text (str): Text zprávy (podporuje Markdown)
            
        Returns:
            bool: True pokud byla zpráva úspěšně odeslána
            
        Raises:
            Exception: Pokud se zprávu nepodařilo odeslat
        """
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            logger.info(f"Zpráva úspěšně odeslána do Telegramu (chat_id: {self.chat_id})")
            return True
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP chyba při odesílání do Telegramu: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Chyba připojení při odesílání do Telegramu: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Chyba při odesílání do Telegramu: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
