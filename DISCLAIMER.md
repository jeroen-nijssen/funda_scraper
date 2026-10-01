# Disclaimer

> **Lees dit voordat je Woningradar gebruikt.**

## Geautomatiseerd scrapen wordt niet ondersteund door de platforms

Woningradar haalt gegevens op bij Funda.nl, Huispedia.nl en Pararius.nl door hun
publieke zoekpagina's op te vragen en de HTML te lezen. **Geen van deze partijen
biedt hiervoor een publieke API aan, en geen van hen ondersteunt of faciliteert
geautomatiseerd scrapen.** Het is goed mogelijk dat het in strijd is met hun
algemene voorwaarden.

Dat betekent concreet:

- **Je gebruikt dit op eigen initiatief en voor eigen risico.** Wie deze software
  draait, is zelf verantwoordelijk voor dat besluit en voor de gevolgen daarvan.
- **Controleer zelf de voorwaarden.** Lees de algemene voorwaarden en het
  `robots.txt` van elke site die je bevraagt, en beoordeel zelf of jouw gebruik
  daarbinnen past. Die voorwaarden kunnen wijzigen zonder dat deze software
  daarop wordt aangepast.
- **Je kunt geblokkeerd worden.** Sites mogen je IP-adres of account blokkeren.
  Dat is een normaal en te verwachten gevolg, geen bug in dit project.
- **De maintainers zijn geen partij.** Deze software wordt geleverd "as is",
  zonder enige garantie, onder de Apache 2.0-licentie. De auteurs en
  bijdragers zijn niet verantwoordelijk of aansprakelijk voor hoe jij de
  software inzet, noch voor blokkades, juridische claims, kosten of andere
  schade die daaruit voortvloeien.

## Bedoeld gebruik

Woningradar is bedoeld als **persoonlijk hulpmiddel**: één huishouden dat zijn
eigen woningzoektocht bijhoudt, met lage frequentie, op een schaal die niet te
onderscheiden is van iemand die de site zelf af en toe bezoekt.

Gebruik het **niet** voor:

- Commerciële doeleinden, doorverkoop van data, of het opbouwen van een eigen
  woningdatabase.
- Het opnieuw publiceren van overgenomen gegevens, foto's of teksten. Die zijn
  auteursrechtelijk beschermd en eigendom van de platforms of de makelaars.
- Hoge frequenties, meerdere parallelle instanties, of het omzeilen van
  botdetectie, rate limits, CAPTCHA's of inlogmuren.

## Wees netjes

De standaardintervallen staan bewust ruim: Funda elk uur, Pararius elk half uur,
Huispedia elk uur. **Verlaag deze niet.** Een woningaanbod verandert niet per seconde,
dus vaker opvragen levert je niets op en belast de site onnodig. Zet je zoekopdracht
zo specifiek mogelijk in (`LOCATION`, `MAX_PRICE`, `MIN_ROOMS`, `MIN_AREA`), zodat
je minder pagina's nodig hebt.

Als een site duidelijk maakt dat dit gebruik niet gewenst is, respecteer dat dan
en stop.

## Geen advies

De opgehaalde informatie kan verouderd, onvolledig of onjuist zijn — bijvoorbeeld
doordat een site zijn HTML heeft aangepast en de parser velden mist. Neem
**altijd** de oorspronkelijke advertentie als bron van waarheid, en baseer geen
financiële of juridische beslissing op de gegevens in Woningradar.

---

## English summary

These platforms do not offer a public API and do not support or condone automated
scraping; doing so may breach their terms of service. You run this software
entirely at your own initiative and risk, and you are responsible for reviewing
each site's terms and `robots.txt` yourself. Being IP-blocked is an expected
outcome, not a bug. The software is provided "as is" under Apache 2.0 with no
warranty, and the authors accept no liability for how you use it.

Intended use is a single household tracking its own house search at low
frequency. Do not use it commercially, do not republish scraped content, do not
run multiple parallel instances, and do not attempt to evade bot detection or
rate limits. Do not lower the default intervals (3600 s Funda, 1800 s Pararius,
3600 s Huispedia). Treat the original listing as the source of truth — parsed data can
be stale or wrong.
