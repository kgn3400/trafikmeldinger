# Trafikmeldinger

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kgn3400/trafikmeldinger)
![GitHub all releases](https://img.shields.io/github/downloads/kgn3400/trafikmeldinger/total)
![GitHub last commit](https://img.shields.io/github/last-commit/kgn3400/trafikmeldinger)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/kgn3400/trafikmeldinger)
[![Validate% with hassfest](https://github.com/kgn3400/trafikmeldinger/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/kgn3400/trafikmeldinger/actions/workflows/hassfest.yaml)

Trafikmeldinger integrationen giver dig mulighed for at se vigtige trafikmeldinger fra [dr.dk/trafik](https://dr.dk/trafik).
Der kan filtreres efter region, transporttype, max timer gamle og ord/sætning der skal matche teksten i trafikmeldingen.

## Installation

For at installere Trafikmeldinger integrationen, søg efter `Trafikmeldinger` i HACS og download.
Eller klik på
[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=Add%20to%20HACS)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kgn3400&repository=trafikmeldinger&category=integration)

Tilføj Trafikmeldinger integrationen til Home Assistant.
[![Åbn Home Assistant og begynd at opsætte en ny integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=trafikmeldinger)

## Konfiguration

Konfiguration opsættes via brugergrænsefladen i Home Assistant.

![Config 1](https://kgn3400.github.io/trafikmeldinger/assets/config_1.png)

![Config 2](https://kgn3400.github.io/trafikmeldinger/assets/config_2.png)

## Sensors

Trafikmeldinger integrationen har følgende sensors:

* `sensor.trafikmeldinger_seneste`
Sensoren viser seneste trafikmelding.

* `sensor.trafikmeldinger_roterende(Er kun aktiveret ved brug af en Timer hjælper)`
Sensoren roterer automatisk til næste trafikmelding. Sensoren er kun aktiv/synlig hvis en [Timer hjælper](https://www.home-assistant.io/integrations/timer/) er oprettet og forbundet med Trafikmeldinger integrationen.

* `sensor.trafikmeldinger_vigtig_besked`
Sensoren viser seneste vigtig meddelelse for hele landet.

> **Bemærk** at hvis filtreringen ikke giver noget umiddelbart resultat, vil sensorne være i ukendt tilstand. Dette kan bruges til at styre om kortet er synlighed.

## Markdown egenskab

Hver sensor har en egenskab som indeholder trafikmeldingen formateret som Markdown.

![Markdown kort konfiguration](https://kgn3400.github.io/trafikmeldinger/assets/md_card_config.png)

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

Følgende aktions er tilgængelige for Trafikmeldinger integrationen:

* `Trafikmeldinger: Marker alt som læst`
* `Trafikmeldinger: Marker alle trafikmeldinger som læst`
* `Trafikmeldinger: Marker alle vigtige meddelelser som læst`
* `Trafikmeldinger: Marker aktuelle trafikmeldinger som læst`
* `Trafikmeldinger: Marker seneste trafikmelding som læst`
* `Trafikmeldinger: Rotere til næste trafikmelding`

## Automations udløsere

Der kan tilføjes en udløser for enheden Trafikmeldinger('Ny trafikmelding' og 'Ny vigtig besked') til en automatisering, som vil blive udløst når der er nye meldinger.

> **Bemærk** det ikke er muligt at have en automation som bruger Trafikmeldinger entiteternes tilstand som udløser. Da entiteternes egenskaber opdateres hver gang der checkes for nye opdateringner. Brug altid de indbyggede udløsere i Trafikmeldinger integrationen.

Følgende udløser hændelses data er tilgængelige for automatiseringen for 'Ny trafikmelding':

```Python
{{ trigger.event.data.ny_melding }}
```

```Python
{{ trigger.event.data.opdateringer }} ## Liste af opdateringer
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

Følgende udløser hændelses data er tilgængelige for automatiseringen for 'Ny vigtig besked':

```Python
{{ trigger.event.data.ny_melding }}
```

```Python
{{ trigger.event.data.oprettet_tidspunkt }}
```

Eksempel på automatisering:

```yaml
alias: Trafikmelding notifikation
description: ""
triggers:
  - device_id: <Indsæt device_id for Trafikmeldinger integrationen her>
    domain: trafikmeldinger
    type: new_traffic_report
    trigger: device
    id: Ny trafikmelding
  - device_id: <Indsæt device_id for Trafikmeldinger integrationen her>
    domain: trafikmeldinger
    type: new_important_notice
    trigger: device
    id: Ny vigtig besked
conditions: []
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - Ny trafikmelding
        sequence:
          - action: notify.persistent_notification
            metadata: {}
            data:
              message: |-
                {{ trigger.event.data.ny_melding }}

                {% if trigger.event.data.opdateringer|length > 0 %}
                Opdatering: {{trigger.event.data.opdateringer[0]}}
                {% endif %}
      - conditions:
          - condition: trigger
            id:
              - Ny vigtig besked
        sequence:
          - action: notify.persistent_notification
            metadata: {}
            data:
              message: "{{ trigger.event.data.ny_melding }} "
mode: single
```

Giv gerne denne integration en stjerne på GitHub, hvis du synes om integration 👍
