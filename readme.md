
<!-- markdownlint-disable MD041 -->
![GitHub release (latest by date)](https://img.shields.io/github/v/release/kgn3400/trafikmeldinger)
![GitHub all releases](https://img.shields.io/github/downloads/kgn3400/trafikmeldinger/total)
![GitHub last commit](https://img.shields.io/github/last-commit/kgn3400/trafikmeldinger)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/kgn3400/trafikmeldinger)
[![Validate% with hassfest](https://github.com/kgn3400/trafikmeldinger/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/kgn3400/trafikmeldinger/actions/workflows/hassfest.yaml)

<img align="left" width="80" height="80" src="https://kgn3400.github.io/trafikmeldinger/assets/icon@2x.png" alt="App icon">

# Trafikmeldinger

<br/>

Trafikmeldinger integrationen giver dig nem adgang til de seneste og vigtigste trafikmeldinger direkte fra [dr.dk/trafik](https://dr.dk/trafik). Med denne integration kan du altid holde dig opdateret om aktuelle trafikale forhold og hændelser i dit område.
Du kan tilpasse visningen af trafikmeldinger ved at filtrere efter:

* 'Region: Vælg én eller flere regioner for kun at se relevante meldinger for dit område.'
* 'Transporttype: Filtrér efter f.eks. vejtrafik, tog, bus eller færge, så du kun ser meldinger for de transportformer, der interesserer dig.'
* 'Maksimal alder: Angiv hvor mange timer gamle meldingerne må være, så du kun får vist de nyeste og mest relevante informationer.'
* 'Søgeord eller sætninger: Indtast specifikke ord eller sætninger, som skal matche teksten i trafikmeldingen, for at fokusere på bestemte hændelser eller emner.'

Med denne fleksible filtrering får du præcis de trafikmeldinger, der er relevante for dig, direkte ind i dit Home Assistant-dashboard.

## Installation

For at installere Trafikmeldinger integrationen, søg efter `Trafikmeldinger` i HACS og download.
Eller klik på
[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=Add%20to%20HACS)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kgn3400&repository=trafikmeldinger&category=integration)

Tilføj Trafikmeldinger integrationen til Home Assistant.
[![Åbn Home Assistant og begynd at opsætte en ny integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=trafikmeldinger)

## Konfiguration

Konfiguration opsættes via brugergrænsefladen i Home Assistant.

<img src="https://kgn3400.github.io/trafikmeldinger/assets/config_1.png" width="400" height="auto" alt="Config 1">
<br/>
Hvis der bruges en [Timer hjælper](https://www.home-assistant.io/integrations/timer/), vil den automatisk rotere til næste trafikmelding. En timer hjælper skal kun bruges hvis der ønskes at synkroniserer med andre integrationer eller kort. Det er vigtigt at timer hjælperen ikke trigger under hvert 15 sekund, da det ellers kan belaste Home Assistant serveren.
<br/>

<img src="https://kgn3400.github.io/trafikmeldinger/assets/config_2.png" width="400" height="auto" alt="Config 2">
<br/>
Angiv ord/sætninger der skal matche trafikmeldingen for at fokusere på bestemte steder eller hændelser. Der foretages kun match på trafikmeldinger og ikke vigtige beskeder.
<br/>

> **Bemærk** at hvis der ingen meldinger eller filtreringen ikke giver noget resultat, vil sensorne være i ukendt tilstand. Dette kan bruges til at styre om kortet er synlighed.

<br/>

<img src="https://kgn3400.github.io/trafikmeldinger/assets/config_3.png" width="400" height="auto" alt="Config 3">
<br/>
<br/>

## Sensors

Trafikmeldinger integrationen har følgende sensors:

* `sensor.trafikmeldinger_vigtig_besked`
Sensoren viser seneste vigtig meddelelse for hele landet.
<br/>

* `sensor.trafikmeldinger_seneste`
Sensoren viser seneste trafikmelding.
<br/>

* `sensor.trafikmeldinger_roterende`
Sensoren roterer automatisk til næste trafikmelding.

## Markdown egenskab

Hver sensor har en egenskab som indeholder trafikmeldingen formateret som Markdown.

![Markdown kort konfiguration](https://kgn3400.github.io/trafikmeldinger/assets/md_card_config.png)

Tilføj et Markdown kort til visningen og indsæt en af de nedenstående Jinja2 skabeloner.

Vigtige beskeder i markdown format:

```Python
{{ state_attr('sensor.trafikmeldinger_vigtig_besked', 'markdown') }}
```

Seneste trafikmelding i markdown format:

```Python
{{ state_attr('sensor.trafikmeldinger_seneste', 'markdown') }}
```

Rotation imellem tidligere trafikmeldinger i markdown format:

```Python
{{ state_attr('sensor.trafikmeldinger_roterende', 'markdown') }}
```

Samlet 0versigt indeholdende vigtige beskeder, seneste trafikmelding og tidligere trafikmeldinger Alt efter hvad der er valgt i konfigurationen i markdown format:

```Python
{{ state_attr('sensor.trafikmeldinger_roterende', 'oversigt_markdown') }}
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

### Support

Hvis du synes godt om denne integration, eller finder den brugbar, må du meget gerne give den en ⭐️ på GitHub 👍 Det vil blive værdsat!
