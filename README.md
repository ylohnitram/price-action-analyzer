[![Price Action Analysis](https://github.com/ylohnitram/price-action-analyzer/actions/workflows/analyze.yml/badge.svg)](https://github.com/ylohnitram/price-action-analyzer/actions/workflows/analyze.yml)

# Price Action Analyzer

Automatizovaný nástroj pro komplexní analýzu price action dat z Binance pomocí AI. Aplikace stahuje OHLCV data, detekuje klíčové price action patterny a generuje podrobnou analýzu tržní struktury s vizualizací možných scénářů, kterou odesílá do Telegram kanálu.

## Funkce

- Stahování OHLCV dat z Binance API
- Tři typy analýz:
  - **Swing analýza** - pro středně a dlouhodobé obchodování:
    - Weekly data (1w) - období 1 roku
    - Daily data (1d) - období 3 měsíců
    - 4-hodinová data (4h) - období 1 měsíce
    - Vizualizace potenciálních scénářů pomocí směrových šipek v grafu
  - **Intraday analýza** - zaměřená na krátkodobé obchodování:
    - 4-hodinová data (4h) - období 1 měsíce (kontext)
    - 30-minutová data (30m) - období 1 týdne
    - 5-minutová data (5m) - období 3 dnů
  - **Single-timeframe analýza** - základní analýza jednoho časového rámce
- Detekce price action patternů:
  - Cenové mezery (Fair Value Gaps)
  - Silné zóny (Order Blocks)
  - Falešné průrazy (Liquidity Sweeps)
  - Swingová high/low
- Generování komplexní analýzy pomocí AI (OpenAI GPT-4)
- Vizualizace supportních/resistenčních zón v grafech
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

#### Swing analýza (všechny časové rámce)
```bash
python main.py -s BTCUSDT --swing
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
- `--swing`: Použít swing analýzu (stahuje data pro všechny časové rámce)
- `--intraday`: Použít intraday analýzu (stahuje data pouze pro 4h, 30m, 5m)
- `-i, --interval`: Časový interval pro single-timeframe analýzu (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- `-d, --days`: Počet dní historie pro single-timeframe analýzu
- `-v, --verbose`: Podrobnější logování
- `--chart-days`: Počet dní k zobrazení v grafu (výchozí: 5)

### Automatizace pomocí GitHub Actions

1. Fork tohoto repozitáře na GitHub

2. Nastavte GitHub Secrets:
   - `OPENAI_API_KEY`
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`

3. Workflow spouští dva typy analýz:
   - Swing analýza: Každý pracovní den v 7:30 UTC
   - Intraday analýza: Každé 2 hodiny během obchodního dne (9:30, 11:30, 13:30, 15:30, 17:30, 19:30, 21:30 UTC)

4. Pro manuální spuštění:
   - Přejděte na záložku "Actions"
   - Vyberte workflow "Price Action Analysis"
   - Klikněte na "Run workflow"
   - Vyberte typ analýzy (swing, intraday, single) a zadejte další požadované parametry

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
│   │   └── price_action.py     # Price action analýza pomocí AI
│   ├── visualization/
│   │   ├── chart_generator.py  # Koordinátor grafů
│   │   ├── charts/            # Specializované typy grafů
│   │   │   ├── base_chart.py
│   │   │   ├── intraday_chart.py
│   │   │   ├── swing_chart.py
│   │   │   └── simple_chart.py
│   │   ├── components/        # Komponenty pro grafy
│   │   │   ├── zones.py       # Podporní a resistenční zóny
│   │   │   └── scenarios.py   # Scénáře budoucího vývoje
│   │   ├── config/           # Konfigurace a nastavení
│   │   └── utils/            # Pomocné funkce
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
- **ChartGenerator**: Vizualizační část - koordinace typů grafů
  - **SwingChart**: Specializovaný graf pro swing obchodování
  - **IntradayChart**: Specializovaný graf pro intraday obchodování
  - **SimpleChart**: Základní graf pro jednoduchou analýzu
- **TelegramBot**: Odesílání notifikací a reportů

Toto rozdělení zajišťuje lepší testovatelnost a udržovatelnost kódu.

## Poslední aktualizace

### Vylepšená vizualizace
- Přepracované vykreslování supportních a resistenčních zón (transparentní obdélníky přes celou šířku grafu)
- Přejmenování "complete" analýzy na "swing" analýzu pro lepší popis jejího účelu
- Modulární architektura grafů umožňující snadné přidávání nových typů grafů
- Vylepšené vykreslování scénářů budoucího vývoje

### Přehlednější struktura kódu
- Rozdělení monolitického kódu na menší, specializované třídy
- Znovu-použitelné komponenty pro vykreslování různých prvků grafu
- Lepší konfigurace barev a stylů

## Licence

MIT
