from hammett.core import Bot
from hammett.core.constants import DEFAULT_STATE

from screens import (
    MainMenuScreen,
    AddLinkScreen,
    RandomLinkScreen,
    AllLinksScreen
)



def main():
    bot = Bot(
        "LinKeeperBot",
        entry_point= MainMenuScreen,
        states = {DEFAULT_STATE: {
            MainMenuScreen,
            AddLinkScreen,
            RandomLinkScreen,
            AllLinksScreen
        },},
    )
    bot.run()

if __name__ == "__main__":
    main()