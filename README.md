[![Price Action Analysis](https://github.com/ylohnitram/price-action-analyzer/actions/workflows/analyze.yml/badge.svg)](https://github.com/ylohnitram/price-action-analyzer/actions/workflows/analyze.yml)

# Price Action Analyzer

Automatizovaný nástroj pro komplexní analýzu price action dat z Binance pomocí AI. Aplikace stahuje OHLCV data, detekuje klíčové price action patterny a generuje podrobnou analýzu tržní struktury s vizualizací možných scénářů, kterou odesílá do Telegram kanálu.

## Funkce

- Stahování OHLCV dat z Binance API
- Dva typy analýz:
  - **Kompletní analýza** - všechny časové rámce:
    - Weekly data (1w) - období 1 roku
    - Daily data (1d) - období 3 měsíců
    - 4-hodinová data (4h) - období 1 měsíce
    - 30-minutová data (30m) - období 1 týdne
    - 5-minutová data (5m) - období 3 dnů
  - **Intraday analýza** - zaměřená na krátkodobé obchodování:
    - 4-hodinová data (4h) - období 1 měsíce (kontext)
    - 30-minutová data (30m) - období 1 týdne
    - 5-minutová data (5m) - období 3 dnů
- Detekce price action patternů:
  - Cenové mezery (Fair Value Gaps)
  - Silné zóny (Order Blocks)
  - Falešné průrazy (Liquidity Sweeps)
  - Swingová high/low
- Generování komplexní analýzy pomocí AI (OpenAI GPT-4)
- Vizualizace potenciálních scénářů pomocí směrových šipek v grafu
- Odesílání výsledků do Telegram kanálu
- Automatické spouštění pomocí GitHub Actions

## Požadavky

- Python 3.8+
- OpenAI API klíč
- Telegram Bot token a chat ID
- GitHub účet (pro automatizaci)

## Instalace

1. Naklonujte repozitář:
   ```bash
   git clone https://github.com/vase-uzivatelske-jmeno/price-action-analyzer.git
   cd price-action-analyzer
   ```

2. Nainstalujte závislosti:
   ```bash
   pip install -r requirements.txt
   ```

3. Nastavte potřebné proměnné prostředí:
   ```bash
   export OPENAI_API_KEY="vas-openai-api-klic"
   export TELEGRAM_TOKEN="vas-telegram-bot-token"
   export TELEGRAM_CHAT_ID="@vas-telegram-kanal"
   ```

## Použití

### Lokální spuštění

#### Kompletní analýza (všechny časové rámce)
```bash
python main.py -s BTCUSDT --complete
```

#### Intraday analýza (pouze 4h, 30m, 5m)
```bash
python main.py -s BTCUSDT --intraday
```

#### Single-timeframe analýza
```bash
python main.py -s BTCUSDT -i 30m -d 7
```

Parametry:
- `-s, --symbol`: Trading pár (např. BTCUSDT, ETHUSDT)
- `--complete`: Použít kompletní analýzu (stahuje data pro všechny časové rámce)
- `--intraday`: Použít intraday analýzu (stahuje data pouze pro 4h, 30m, 5m)
- `-i, --interval`: Časový interval pro single-timeframe analýzu (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- `-d, --days`: Počet dní historie pro single-timeframe analýzu
- `-v, --verbose`: Podrobnější logování
- `--chart-days`: Počet dní k zobrazení v grafu (výchozí: 2)

### Automatizace pomocí GitHub Actions

1. Fork tohoto repozitáře na GitHub

2. Nastavte GitHub Secrets:
   - `OPENAI_API_KEY`
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`

3. Workflow spouští dva typy analýz:
   - Kompletní analýza: Každý pracovní den v 7:30 UTC
   - Intraday analýza: Každé 2 hodiny během obchodního dne (9:30, 11:30, 13:30, 15:30, 17:30, 19:30, 21:30 UTC)

4. Pro manuální spuštění:
   - Přejděte na záložku "Actions"
   - Vyberte workflow "Price Action Analysis"
   - Klikněte na "Run workflow"
   - Vyberte typ analýzy (complete, intraday, single) a zadejte další požadované parametry

## Struktura projektu

```
price-action-analyzer/
├── .github/
│   └── workflows/
│       └── analyze.yml     # GitHub Actions workflow
├── src/
│   ├── clients/
│   │   └── binance_client.py   # Klient pro Binance API
│   ├── analysis/
│   │   └── price_action.py     # Price action analýza
│   ├── visualization/
│   │   └── chart_generator.py  # Generování grafů
│   ├── notification/
│   │   └── telegram_bot.py     # Telegram notifikace
│   └── utils/
│       └── helpers.py          # Pomocné funkce
├── main.py                # Hlavní skript
├── requirements.txt       # Závislosti
└── README.md              # Dokumentace
```

## Architektura

Aplikace je rozdělena do několika modulů s jasně definovanou zodpovědností:

- **BinanceClient**: Stahování dat z Binance API
- **PriceActionAnalyzer**: Analytická část - zpracování dat, detekce patternů, generování textové analýzy
- **ChartGenerator**: Vizualizační část - generování grafů s cenovými zónami a šipkami s potenciálními scénáři
- **TelegramBot**: Odesílání notifikací a reportů

Toto rozdělení zajišťuje lepší testovatelnost a udržovatelnost kódu.

## Nové funkce v poslední verzi

### Vizualizace scénářů

- V kompletní analýze jsou nyní zobrazeny potenciální scénáře vývoje ceny pomocí barevných šipek v grafu
- Bullish scénáře jsou znázorněny zelenými šipkami směřujícími vzhůru
- Bearish scénáře jsou znázorněny červenými šipkami směřujícími dolů
- Grafy obsahují jasné označení klíčových cenových zón a frekventovaných oblastí

### Vylepšená detekce patternů

- Přesnější identifikace Fair Value Gaps (FVG)
- Lepší rozpoznávání Order Blocks (OB)
- Detekce swingových high/low bodů
- Pokročilé označení falešných průrazů (liquidity sweeps)

### Přizpůsobené výstupy

- Kompletní analýza se zaměřuje na identifikaci zón a potenciálních scénářů bez konkrétních vstupů
- Intraday analýza stále poskytuje konkrétní obchodní příležitosti s přesnými úrovněmi

## Příklad výstupu

### Kompletní analýza

```
**Kompletní Price Action Analýza BTCUSDT**

## DLOUHODOBÝ TREND (Weekly/Daily)

### Klíčové úrovně
- **Supportní zóny**:
  - 64,500-65,200 (silná objemová zóna)
  - 62,800-63,300 (bývalá rezistence, nyní support)
  - 59,200-59,800 (významná akumulační zóna)
  - 57,400-57,800 (týdenní demand zóna)
  
- **Resistenční zóny**:
  - 67,400-67,800 (medvědí order block)
  - 69,200-69,800 (silný supply level)
  - 71,500-72,000 (bývalý ATH rezistence)
  - 73,600-74,000 (současný ATH)

- **Fair Value Gaps**:
  - Bullish FVG: 66,400-66,900 (nevyplněná mezera z 20.2.)
  - Bearish FVG: 70,200-70,600 (nevyplněná mezera ze 7.3.)

### Tržní struktura
- BTC je v dlouhodobém býčím trendu od Q4 2023
- Aktuálně se nachází v konsolidační fázi po dosažení ATH
- Tvorba vyšších low naznačuje pokračující sílu býků
- Klesající volume během poslední konsolidace naznačuje vyčerpání prodejců

## STŘEDNĚDOBÝ KONTEXT (4h)

- Formování sestupného klínu (bullish reversal pattern)
- Série nižších high/low v krátkodobém downtrend
- Klíčové objemové klastry na úrovních:
  - 65,200-65,600 (vysoký objem nákupů)
  - 68,800-69,200 (vysoký objem prodejů)
- Významná formace double bottom na 63,800

## MOŽNÉ SCÉNÁŘE

### BULLISH SCÉNÁŘ
- Spouštěč: Průraz nad 67,500 s rostoucím objemem
- Primární cíl: 69,200-69,800
- Sekundární cíl: 71,500-72,000
- Konfirmace: Uzavření denní svíčky nad 67,800

### BEARISH SCÉNÁŘ
- Spouštěč: Ztráta supportu 64,500 a close pod touto úrovní
- Primární cíl: 62,800-63,300
- Sekundární cíl: 59,200-59,800
- Konfirmace: Uzavření denní svíčky pod 64,200

### NEUTRÁLNÍ SCÉNÁŘ
- Pokračování konsolidace v rozmezí 64,500-67,500
- Očekávané testování obou krajních úrovní
- Klíčové pro sledování: vývoj objemu na extrémech rozsahu

## DŮLEŽITÉ OBLASTI KE SLEDOVÁNÍ

- Denní pivot point: 65,850
- Klíčové swingové body:
  - Swing low: 63,800 (16.2. a 22.2.)
  - Swing high: 69,400 (2.3.)
- Liquidity pool pod 63,500 (potenciální stop hunt area)
- Liquidity pool nad 70,000 (potenciální stop hunt area)

Čas analýzy: 2024-02-26 15:30 UTC
```

### Intraday analýza

```
**Intraday Price Action Analýza BTCUSDT**

## KRÁTKODOBÝ TREND A KONTEXT (4h)

- **Struktura trhu**: Cena se nachází v krátkodobém rostoucím trendu s vytvořením vyšších low/high
- **Klíčové úrovně**:
  - Support: 64,800-65,000 (bývalá resistance, nyní support)
  - Resistance: 66,400-66,600 (významná zóna odmítnutí)
- **Objemový profil**: Rostoucí objem při pohybu vzhůru, svědčí o síle trendu

## INTRADAY PŘÍLEŽITOSTI (30m)

- **Aktuální situace**: Konsolidace po bull runu z $64,500 na $66,200
- **Klíčové patterny**:
  - Falešný průraz $66,000 s rychlým návratem a objemem
  - Silná býčí zóna na $65,400-$65,500 (triple bottom)
- **Objemová divergence**: Klesající objem během konsolidace naznačuje možný pokračující pohyb

## SCALPING SETUPS (5m)

- **Bull Flag** formace na 5m timeframe
- **Order Block** na $65,650 s 90% tělem svíčky
- **Cenová mezera** mezi $65,800-$65,900 (nevyplněný gap)

## KONKRÉTNÍ OBCHODNÍ PŘÍLEŽITOSTI

1. **Breakout Long**
   - Vstup: Při průrazu $66,200 s rostoucím objemem
   - Potvrzení: Uzavření 5m svíčky nad úrovní
   - Stop Loss: $65,950
   - Take Profit: $66,500 (TP1), $66,700 (TP2)
   - Platnost: 6 hodin

2. **Pullback Long**
   - Vstup: $65,650 (Order Block)
   - Stop Loss: $65,450
   - Take Profit: $66,200
   - Platnost: 4 hodiny

Čas analýzy: 2024-02-26 14:30 UTC
```

## Licence

MIT
