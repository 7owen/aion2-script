import argparse

from bot_config import RoleType, config
from bot_runner import BotRunner
from factories import SkillFactory, create_role, create_strategy
from game_context import BotState
from km_driver import KmboxDriver
from player_actions import PlayerActions
from vision_client import VisionClient


class Aion2Bot:
    """组合应用依赖，并管理运行期资源。"""

    def _create_runner(self, km_driver: KmboxDriver) -> BotRunner:
        vision_client = VisionClient()
        player_action = PlayerActions(km_driver, vision_client)
        skill_factory = SkillFactory(km_driver)
        role = create_role(player_action, skill_factory)
        state = BotState(role)
        strategy = create_strategy(state)

        return BotRunner(
            state=state,
            video_capture=None,
            player_action=player_action,
            strategy=strategy,
            vision_client=vision_client,
        )

    def run(self) -> None:
        km_driver = KmboxDriver()

        try:
            runner = self._create_runner(km_driver)
            runner.run()
        finally:
            self._close_resources(km_driver)

    @staticmethod
    def _close_resources(
        km_driver: KmboxDriver,
    ) -> None:
        km_driver.close()


def main():
    parser = argparse.ArgumentParser(description="Aion2 Bot Runner")
    parser.add_argument(
        "--role",
        type=str,
        choices=["swordstar", "bowstar"],
        help="角色类型 (swordstar 或 bowstar)",
    )

    args = parser.parse_args()

    if args.role:
        config.mode.role_type = RoleType(args.role)

    Aion2Bot().run()


if __name__ == "__main__":
    main()
