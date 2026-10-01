<p align="center">
  <img src="assets/banner.svg" alt="Woningradar — Nieuwe woningen op je radar" width="720">
</p>

<p align="center">
  Houdt Funda, Huispedia en Pararius voor je in de gaten en zet elke nieuwe woning
  automatisch op een Kanban-bord.
</p>

---

> [!WARNING]
> Funda, Huispedia en Pararius bieden geen API aan en **ondersteunen geen
> geautomatiseerd scrapen**. Je gebruikt dit project op eigen initiatief en voor
> eigen risico. Lees eerst de **[disclaimer](DISCLAIMER.md)**.

## Wat doet het?

Woningradar controleert elk uur of er nieuwe koopwoningen zijn bijgekomen die
passen bij jouw zoekopdracht. Elke nieuwe woning komt als kaartje op een
Kanban-bord (Kanboard) te staan, zodat je ze rustig kunt doorlopen:

```
Nieuw binnen  →  In beoordeling  →  Interessant  /  Niet interessant
```

Woningen die al op het bord staan worden niet nogmaals toegevoegd, dus je ziet
alleen wat echt nieuw is.

**Wat je nodig hebt:** een computer of server die aan blijft staan, met
[Docker](https://docs.docker.com/get-docker/) en Docker Compose erop.

## Snel starten

### 1. Download het project

```bash
git clone https://github.com/jeroen-nijssen/funda_scraper.git
cd funda_scraper
```

### 2. Stel je zoekopdracht in

Maak een `.env`-bestand aan op basis van het voorbeeld:

```bash
cp .env.example .env
```

Open `.env` en pas je zoekcriteria aan. Voor Amsterdam, maximaal 5 km eromheen,
tot € 450.000:

```ini
LOCATION=gemeente-amsterdam
DISTANCE=5
MAX_PRICE=450000
MIN_ROOMS=5
MIN_AREA=100
```

### 3. Start alles op

```bash
./woningradar.sh run
```

Dit doet in één keer:

1. Kanboard starten
2. Wachten tot Kanboard klaar is
3. Het project **Property Listings** en de vier kolommen aanmaken
4. De scraper starten

Je hoeft dus niets handmatig in te richten.

### 4. Zet het juiste project-ID in `.env`

Bij stap 3 wordt een project-ID getoond, bijvoorbeeld:

```
Project ID   : 1
Set KANBAN_PROJECT_ID=1 in your .env file so the
scraper writes listings to this project.
```

Staat daar een ander nummer dan `1`? Zet dat nummer dan in `.env` als
`KANBAN_PROJECT_ID` en herstart met `./woningradar.sh stop` en
`./woningradar.sh run`. Anders komen de woningen op het verkeerde bord terecht.

Het ID zien als je het gemist hebt:

```bash
./woningradar.sh logs
```

### 5. Bekijk je bord

Ga naar **http://localhost:8080** en log in met `admin` / `admin`.

> [!CAUTION]
> Wijzig dit wachtwoord direct, en zet poort 8080 nooit open op internet. Zie
> [SECURITY.md](SECURITY.md).

De eerste woningen verschijnen binnen een uur. Er staat pas iets op het bord
zodra er daadwerkelijk een *nieuwe* woning is gevonden.

## Dagelijks gebruik

| Commando | Wat het doet |
| --- | --- |
| `./woningradar.sh run` | Alles starten |
| `./woningradar.sh stop` | Alles stoppen |
| `./woningradar.sh status` | Draait alles nog? Inclusief statistieken per site |
| `./woningradar.sh logs` | Live meekijken wat er gebeurt |
| `./woningradar.sh health` | Snelle controle of de scraper leeft |
| `./woningradar.sh kanboard` | Kanboard openen in je browser |
| `./woningradar.sh setup` | Bord opnieuw inrichten (veilig, verwijdert niets) |
| `./woningradar.sh build` | Docker-image opnieuw bouwen na een update |

Voor ontwikkelaars zijn er ook `test`, `lint`, `shell`, `workers`,
`detailed-status` en `kanboard-logs`. Zie `./woningradar.sh` zonder argument.

## Zoekopdracht instellen

Alle instellingen staan in `.env`.

### Waar en wat je zoekt

| Instelling | Betekenis | Standaard |
| --- | --- | --- |
| `LOCATION` | Gemeente, met `gemeente-` ervoor | `gemeente-amsterdam` |
| `DISTANCE` | Zoekstraal in kilometers | `5` |
| `MAX_PRICE` | Maximale vraagprijs in euro's | `450000` |
| `MIN_ROOMS` | Minimaal aantal kamers | `5` |
| `MIN_AREA` | Minimale woonoppervlakte in m² | `100` |

### Hoe vaak er gekeken wordt

| Instelling | Betekenis | Standaard |
| --- | --- | --- |
| `FUNDA_SLEEP` | Wachttijd na Funda, in seconden | `3600` (1 uur) |
| `PARARIUS_SLEEP` | Wachttijd na Pararius, in seconden | `1800` (30 min) |
| `HUISPEDIA_SLEEP` | Wachttijd na Huispedia, in seconden | `3600` (1 uur) |

> [!WARNING]
> **Verlaag deze waarden niet.** Vaker opvragen levert je geen woningen extra op
> — het aanbod verandert niet per minuut — maar belast de sites wel en vergroot
> de kans dat je IP-adres wordt geblokkeerd. Zie de [disclaimer](DISCLAIMER.md).

### Kanboard-instellingen

| Instelling | Betekenis | Standaard |
| --- | --- | --- |
| `KANBAN_PROJECT_ID` | Op welk project de woningen komen | `1` |
| `KANBAN_USERNAME` | Gebruikersnaam | `admin` |
| `KANBAN_PASSWORD` | Wachtwoord — **wijzig dit** | `admin` |
| `KANBAN_BASE_URL` | Adres van Kanboard binnen Docker | `http://kanboard` |
| `KANBAN_URL` | JSON-RPC-adres van Kanboard | `http://kanboard/jsonrpc.php` |
| `KANBAN_PROJECT_NAME` | Naam van het aan te maken project | `Property Listings` |
| `KANBAN_OWNER_ID` | Wie de kaartjes toegewezen krijgt | `1` |
| `KANBAN_CREATOR_ID` | Wie als aanmaker geldt | `1` |

Draai je `setup_kanboard.py` los van Docker, zet dan
`KANBAN_BASE_URL=http://localhost:8080`.

## Problemen oplossen

### Er komen geen woningen op het bord

Meestal is er simpelweg niets nieuws. Controleer eerst of de scraper draait en
of er fouten zijn:

```bash
./woningradar.sh status
```

Zie je `runs` oplopen en `errors` op 0 staan, dan werkt alles. Loop daarna na:

- **Is je zoekopdracht te streng?** Probeer `MAX_PRICE` te verhogen of
  `MIN_ROOMS` en `MIN_AREA` te verlagen.
- **Staat `KANBAN_PROJECT_ID` goed?** Zie [stap 4](#4-zet-het-juiste-project-id-in-env).
  Dit is de meest voorkomende oorzaak.
### Funda vindt niets

Funda.nl blokkeert geautomatiseerde requests met een bot-check op CDN-niveau.
De Funda-scraper rendert pagina's daarom met een headless browser (Playwright)
om dit te omzeilen, maar dit is **best-effort en niet gegarandeerd te werken**
— in tests leverde dit nog steeds de bot-check-pagina op in plaats van echte
resultaten. Het kan zijn dat dit vanaf jouw netwerk wel werkt. Zie dit niet als
een bevestigde fix.

### Eén site vindt plotseling niets meer

Dan heeft die site zijn website verbouwd. Woningradar leest de HTML van de
zoekpagina's, en zodra de opbouw daarvan verandert, herkent hij de woningen niet
meer. Dit hoort bij scrapen zonder API.

De andere sites blijven gewoon werken. Meld het via een
[issue](https://github.com/jeroen-nijssen/funda_scraper/issues/new/choose) —
kies **Scraper broken**.

### Foutmeldingen in de logs

```bash
./woningradar.sh logs
```

- `No listings found` — geen resultaten, of de HTML is gewijzigd (zie hierboven).
- `Request attempt 1 failed` — tijdelijke netwerkfout. Er wordt automatisch
  opnieuw geprobeerd; incidenteel is dit normaal.
- `Error creating Kanban task` — controleer `KANBAN_PASSWORD` en
  `KANBAN_PROJECT_ID` in `.env`.
- Blijft het misgaan bij álle sites? Dan kan je IP-adres geblokkeerd zijn. Zet
  het even uit en verlaag de frequentie niet.

Logbestanden staan in de map `logs/`.

### Opnieuw beginnen

```bash
./woningradar.sh stop
./woningradar.sh run
```

Je bord en kaartjes blijven bewaard. `./woningradar.sh setup` opnieuw uitvoeren
is veilig: bestaande kolommen en kaartjes worden nooit verwijderd.

## Hoe het werkt

```
                  ┌──────────────────────────────┐
                  │  Woningradar (poort 8000)    │
                  │                              │
   Funda.nl  ◀────┤  Funda-worker      elk uur   │
Pararius.nl  ◀────┤  Pararius-worker   elk 30m   │──┐
Huispedia.nl ◀────┤  Huispedia-worker  elk uur   │  │
                  │                              │  │ JSON-RPC
                  │  Monitor + /health /status   │  │
                  └──────────────────────────────┘  │
                                                    ▼
                                    ┌──────────────────────────────┐
                                    │  Kanboard (poort 8080)       │
                                    │  Nieuw → Beoordeling →       │
                                    │  Interessant / Niet          │
                                    └──────────────────────────────┘
```

Elke site heeft zijn eigen worker met zijn eigen tempo. Valt één worker uit, dan
blijven de andere doorwerken en wordt de uitvaller automatisch herstart. Voor elke
gevonden woning wordt eerst op het bord gecontroleerd of die er al staat.

## Meedoen en ontwikkelen

Ontwikkeling gebeurt in het Engels; alleen deze gebruikersdocumentatie is in het
Nederlands. Zie:

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — opzetten, tests, een site toevoegen
- **[DISCLAIMER.md](DISCLAIMER.md)** — voorwaarden en verantwoord gebruik
- **[SECURITY.md](SECURITY.md)** — kwetsbaarheden melden, veilig inrichten
- **[CHANGELOG.md](CHANGELOG.md)** — wat er per versie is gewijzigd

Snelle start voor ontwikkelaars:

```bash
pip install -r requirements-dev.txt
pytest          # vanuit de hoofdmap van het project
ruff check .
```

## Licentie

[Apache 2.0](LICENSE). Geleverd zonder garantie; zie de
[disclaimer](DISCLAIMER.md).
