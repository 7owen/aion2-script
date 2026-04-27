from bot_runner import BotRunner
from factories import SkillFactory, create_role, create_strategy
from game_context import BotState
from km_driver import KmboxDriver
from player_actions import PlayerActions


class Aion2Bot:
    """组合应用依赖，并管理运行期资源。"""

    def _create_runner(
        self, km_driver: KmboxDriver
    ) -> BotRunner:
        player_action = PlayerActions(km_driver)
        skill_factory = SkillFactory(km_driver)
        role = create_role(player_action, skill_factory)
        state = BotState(role)
        strategy = create_strategy(state)

        return BotRunner(
            state=state,
            video_capture=None,
            player_action=player_action,
            strategy=strategy,
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
    Aion2Bot().run()


if __name__ == "__main__":
    main()
