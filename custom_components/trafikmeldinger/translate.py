"""Hmmm."""

from pathlib import Path
from typing import Any

import aiofiles
import orjson

from homeassistant.components.frontend import storage as frontend_store
from homeassistant.core import HomeAssistant


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class Translate:
    """Translate."""

    __language: str = ""
    __json_dict: dict[str, Any] = {}
    acive_language: str = ""

    def __init__(self, hass: HomeAssistant, load_only: str = "") -> None:
        """Init."""
        self.hass = hass
        self.load_only: str = load_only

    # ------------------------------------------------------------------
    async def async_get_localized_str(
        self,
        key: str,
        language: str | None = None,
        file_name: str = ".json",
        load_only: str = "",
        default: Any = "",
        **kvargs,
    ) -> str:
        """Get localized string."""

        if load_only == "":
            load_only = self.load_only

        if language is None:
            language = self.hass.config.language

            owner = await self.hass.auth.async_get_owner()

            if owner is not None:
                _, owner_data = await frontend_store.async_user_store(
                    self.hass, owner.id
                )

                if "language" in owner_data and "language" in owner_data["language"]:
                    language = owner_data["language"]["language"]

        await self.__async_check_language_loaded(
            str(language), file_name=file_name, load_only=load_only
        )

        if len(kvargs) == 0:
            return Translate.__json_dict.get(key, default)

        return str(Translate.__json_dict.get(key, default)).format(**kvargs)

    # ------------------------------------------------------------------
    async def __async_check_language_loaded(
        self, language: str, file_name: str = ".json", load_only: str = ""
    ) -> None:
        """Check language."""

        # ------------------------------------------------------------------
        def recursive_flatten(
            prefix: Any, data: dict[str, Any], load_only: str = ""
        ) -> dict[str, Any]:
            """Return a flattened representation of dict data."""
            output = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    output.update(
                        recursive_flatten(f"{prefix}{key}.", value, load_only)
                    )
                elif (
                    load_only != "" and f"{prefix}{key}".find(load_only) == 0
                ) or load_only == "":
                    output[f"{prefix}{key}"] = value
            return output

        if Translate.__language != language:
            Translate.__language = language

            filename = (
                Path(Path(__file__).parent) / "translations" / (language + file_name)
            )
            if filename.is_file():
                async with aiofiles.open(str(filename)) as json_file:
                    Translate.__json_dict = recursive_flatten(
                        "", orjson.loads(await json_file.read()), load_only
                    )
                Translate.acive_language = language
                return

            filename = Path(Path(__file__).parent) / "translations" / ("en" + file_name)
            if filename.is_file():
                async with aiofiles.open(str(filename)) as json_file:
                    Translate.__json_dict = recursive_flatten(
                        "", orjson.loads(await json_file.read()), load_only
                    )
                Translate.acive_language = "en"
                return
