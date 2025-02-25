# Multi-Timeframe Price Action Analyzer

Automatizovaný nástroj pro komplexní analýzu price action dat z Binance pomocí AI. Aplikace stahuje OHLCV data pro různé časové rámce, detekuje klíčové price action patterny a generuje podrobnou multi-timeframe analýzu, kterou odesílá do Telegram kanálu.

## Funkce

- Stahování OHLCV dat z Binance API
- Multi-timeframe analýza přesně dle požadavků:
  - Weekly data (1w) - období 1 roku
  - Daily data (1d) - období 3 měsíců
  - 4-hodinová data (4h) - období 1 měsíce
  - 30-minutová data (30m) - období 1 týdne
  - 5-minutová data (5m) - období 3 dnů
- Detekce price action patternů:
  - Cenové mezery (Fair Value Gaps)
  - Silné zóny (Order Blocks)
  - Falešné průrazy (Liquidity Sweeps)
- Generování komplexní analýzy pomocí AI (OpenAI GPT-4)
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
   git clone https://github.com/ylohnitram/price-action-analyzer.git
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

#### Multi-timeframe analýza (doporučeno)
```bash
python main.py -s BTCUSDT --multi
```

#### Single-timeframe analýza
```bash
python main.py -s BTCUSDT -i 30m -d 7
```

Parametry:
- `-s, --symbol`: Trading pár (např. BTCUSDT, ETHUSDT)
- `--multi`: Použít multi-timeframe analýzu (stahuje data pro všechny časové rámce)
- `-i, --interval`: Časový interval pro single-timeframe analýzu (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- `-d, --days`: Počet dní historie pro single-timeframe analýzu
- `-v, --verbose`: Podrobnější logování

### Automatizace pomocí GitHub Actions

1. Fork tohoto repozitáře na GitHub

2. Nastavte GitHub Secrets:
   - `OPENAI_API_KEY`
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`

3. Workflow se automaticky spustí podle nastaveného rozvrhu (každých 8 hodin)

4. Pro manuální spuštění:
   - Přejděte na záložku "Actions"
   - Vyberte workflow "Multi-Timeframe Price Action Analysis"
   - Klikněte na "Run workflow"
   - Zadejte požadované parametry

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
│   ├── notification/
│   │   └── telegram_bot.py     # Telegram notifikace
│   └── utils/
│       └── helpers.py          # Pomocné funkce
├── main.py                # Hlavní skript
├── requirements.txt       # Závislosti
└── README.md              # Dokumentace
```

## Příklad výstupu

### Multi-Timeframe Analýza

```
**Multi-Timeframe Price Action Analýza BTCUSDT**

## Tržní kontext (Weekly/Daily)

### Dlouhodobý trend
- **Weekly**: BTC se nachází v býčím trendu od října 2023 ($25,400 → $73,800)
- **Poslední týdny**: Konsolidace po dosažení ATH $73,800, s podporou na úrovni $63,200
- **Hlavní S/R zóny**:
  - Support: $63,200 (dvojité dno na týdenním timeframe)
  - Support: $59,400 (významná akumulační zóna z ledna 2024)
  - Resistance: $73,800 (ATH)

### Daily timeframe
- Formace **býčí vlajky** - typický konsolidační pattern v býčím trendu
- Poslední 2 týdny se cena pohybuje v klesajícím klínu
- Významný objemový cluster na $64,500 (oblast nakupování)

## Střednědobý pohled (4h)

- **Struktura trhu**: Série nižších high/low (krátkodobý medvědí trend)
- **Klíčové zóny**:
  - Support: $64,200-$63,900 (silná zóna s vysokým objemem)
  - Resistance: $66,800-$67,200 (úroveň odmítnutí s falešným průrazem)
- **Cenové mezery**: Významná mezera na $65,700-$66,100
- **Objemový profil**: Klesající objem během klesajícího trendu naznačuje vyčerpání prodejců

## Krátkodobé příležitosti (30m/5m)

### 30m Timeframe
- **Silná býčí zóna** na $64,100-$64,300 (3 zamítnutí medvědů)
- **Falešný průraz** minima z 12.3. ($63,900)
- **Potenciální vstup**: Long nad $64,500 s SL pod $63,800

### 5m Timeframe
- **Cenová mezera** detekována mezi $64,700-$64,850
- **Bullish Order Block** na $64,200 (s 85% tělem a rostoucím objemem)
- **Falešný průraz** na $64,000 následovaný rychlým návratem

## Obchodní příležitosti

1. **Dlouhodobé**: Akumulace v zóně $63,200-$64,500 s cílem na ATH ($73,800)
2. **Střednědobé**: Long nad $64,800 (průraz klesajícího klínu) s cílem $67,000
3. **Krátkodobé**: 
   - Long: Vstup $64,300, SL $63,900, cíle $65,400 a $66,800
   - Short: Pouze pod $63,700 s prudkým nárůstem objemu
   
Čas analýzy: 2024-03-16 15:30 UTC
```

### Single-Timeframe Analýza

```
**Price Action Analýza BTCUSDT (30m)**

1. **Významná cenová struktura**
   - Vytvoření vyšších low (15:30, 16:15, 17:00 UTC)
   - Konsolidace pod resistancí $66,800
   - Klíčová supportní zóna: $66,400-$66,500

2. **Detekované patterny**
   - Bullish Order Block na $66,450 (15:45 UTC)
   - False Low Breakout na $66,350 (16:30 UTC)
   - Inside Bar formace (17:15-17:45 UTC)

3. **Objemová analýza**
   - Klesající objem během konsolidace (typicky předchází pohybu)
   - Volume spike na $66,350 (akumulace na supportu)
   - Nízký volume na resistance = slabý prodejní tlak

4. **Supporty a resistance**
   - S1: $66,450 (Order Block)
   - S2: $66,350 (False Breakout Low)
   - R1: $66,800 (Intraday High)
   - R2: $67,000 (Psychologická úroveň)

5. **Obchodní příležitosti**
   - Long nad $66,550 (průraz Inside Bar formace)
   - Stop Loss pod $66,450 (pod Order Block)
   - Cíle: $66,800 a $67,000

Čas analýzy: 2024-03-16 18:00 UTC
```

## Licence

MIT
