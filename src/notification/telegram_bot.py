#!/usr/bin/env python3

import requests
import logging
import os

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

    def send_message_with_image(self, text, image_path):
        """
        Odešle zprávu s obrázkem do Telegram chatu/kanálu.
        
        Args:
            text (str): Text zprávy (podporuje Markdown)
            image_path (str): Cesta k obrázku
            
        Returns:
            bool: True pokud byla zpráva úspěšně odeslána
            
        Raises:
            Exception: Pokud se zprávu nepodařilo odeslat
        """
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        
        # Kontrola, zda soubor existuje
        if not os.path.exists(image_path):
            error_msg = f"Soubor s obrázkem neexistuje: {image_path}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Kontrola, zda text není příliš dlouhý
        if len(text) > 1024:
            logger.warning(f"Text je příliš dlouhý pro caption (má {len(text)} znaků, limit je 1024). Ořezávám.")
            # Oříznutí textu na 1000 znaků + "..."
            text = text[:1000] + "..."
        
        try:
            with open(image_path, 'rb') as image_file:
                files = {'photo': image_file}
                data = {
                    "chat_id": self.chat_id,
                    "caption": text,
                    "parse_mode": "Markdown"
                }
                
                response = requests.post(url, data=data, files=files)
                response.raise_for_status()
            
            logger.info(f"Zpráva s obrázkem úspěšně odeslána do Telegramu (chat_id: {self.chat_id})")
            return True
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP chyba při odesílání obrázku do Telegramu: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Chyba připojení při odesílání obrázku do Telegramu: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Chyba při odesílání obrázku do Telegramu: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def send_analysis_with_chart(self, analysis, chart_path):
        """
        Odešle analýzu s grafem do Telegram chatu/kanálu.
        
        Pokud je analýza příliš dlouhá pro caption u obrázku, rozdělí ji
        na dvě zprávy - první s textem a druhou s obrázkem.
        
        Args:
            analysis (str): Text analýzy (podporuje Markdown)
            chart_path (str): Cesta ke grafu
            
        Returns:
            bool: True pokud byly zprávy úspěšně odeslány
        """
        # Pokud je analýza příliš dlouhá pro caption (limit 1024 znaků)
        if len(analysis) > 1024:
            # Nejprve pošleme samotnou analýzu
            self.send_message(analysis)
            
            # Pak pošleme graf s krátkým popisem
            caption = "📊 *Svíčkový graf s vyznačenými zónami*"
            self.send_message_with_image(caption, chart_path)
        else:
            # Jinak pošleme vše v jedné zprávě
            self.send_message_with_image(analysis, chart_path)
        
        return True
