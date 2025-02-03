# Trafikmeldinger

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kgn3400/trafikmeldinger)
![GitHub all releases](https://img.shields.io/github/downloads/kgn3400/trafikmeldinger/total)
![GitHub last commit](https://img.shields.io/github/last-commit/kgn3400/trafikmeldinger)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/kgn3400/trafikmeldinger)
[![Validate% with hassfest](https://github.com/kgn3400/trafikmeldinger/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/kgn3400/trafikmeldinger/actions/workflows/hassfest.yaml)

Trafikmeldinger integrationen giver dig mulighed for at se vigtige trafikmeldinger fra [dr.dk/trafik](https://dr.dk/trafik).
Der kan filtreres efter region, transporttype, max timer gamle og ord/sætning der skal matche teksten i trafikmeldingen.

## Installation

For installationsvejledning, indtil Trafikmeldinger integrationen bliver en del af HACS, [se denne guide](https://hacs.xyz/docs/faq/custom_repositories).
Eller klik på
[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=Add%20to%20HACS)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kgn3400&repository=trafikmeldinger&category=integration)

Tilføj Trafikmeldinger integrationen til Home Assistant.
[![Åbn Home Assistant og begynd at opsætte en ny integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=trafikmeldinger)

## Konfiguration

Konfiguration opsættes via brugergrænsefladen i Home Assistant.

![Config 1](https://github.com/kgn3400/trafikmeldinger/blob/main/assets/config_1.png)

For at kunne aktiverer rotations sensoren, skal der oprettes eller være oprettet en [Timer hjælper](https://www.home-assistant.io/integrations/timer/).

![Config 2](https://github.com/kgn3400/trafikmeldinger/blob/main/assets/config_2.png)

## Sensors

Trafikmeldinger integrationen har følgende sensors:

* `sensor.trafikmeldinger_seneste`
* `sensor.trafikmeldinger_roterende(Er kun aktiveret ved brug af en Timer hjælper)`
* `sensor.trafikmeldinger_vigtig_besked`

Bemærk at hvis filtreringen ikke giver noget resultat, vil sensorne være i ukendt tilstand. Dette kan bruges til at styre om kortet er synlighed.

## Markdown egenskab

Hver sensor har en attribut som indeholder trafikmeldingen formateret som Markdown.

![Markdown kort konfiguration](https://github.com/kgn3400/trafikmeldinger/blob/main/assets/md_card_config.png)

Tilføj et Markdown kort til visningen og indsæt en af de nedenstående Jinja2 skabeloner.

```Python
{{ state_attr('sensor.trafikmeldinger_roterende', 'markdown') }}
```

```Python
{{ state_attr('sensor.trafikmeldinger_seneste', 'markdown') }}
```

```Python
{{ state_attr('sensor.trafikmeldinger_vigtig_besked', 'markdown') }}
```

## Aktions

Følgende aktions er tilgængelige for Trafikmedlinger integrationen:

* `Trafikmeldinger: Marker alt som læst`
* `Trafikmeldinger: Marker alle trafikmeldinger som læst`
* `Trafikmeldinger: Marker alle vigtige meddelelser som læst`
* `Trafikmeldinger: Marker aktuelle trafikmeldinger som læst`
* `Trafikmeldinger: Marker seneste trafikmelding som læst`
* `Trafikmeldinger: Rotere til næste trafikmelding`

## Udløser

Det er muligt at tilføje en udløser til en automatiseringer for Trafikmeldinger(Ny trafikmelding).

Følgende udløser hændelses data er tilgængelige for automatiseringen:

```Python
{{ trigger.event.data.ny_trafikmelding }}
```

```Python
{{ trigger.event.data.reference_tekst }}
```

```Python
{{ trigger.event.data.region }}
```

```Python
{{ trigger.event.data.transporttype }}
```

```Python
{{ trigger.event.data.oprettet_tidspunkt }}
```
