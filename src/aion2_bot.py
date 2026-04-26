from bot_runner import BotRunner
from factories import SkillFactory, create_role, create_strategy
from game_context import BotState
from image_engine import ImageEngine
from km_driver import KmboxDriver
from player_actions import PlayerActions
from video_capture import VideoCapture


class Aion2Bot:
    """组合应用依赖，并管理运行期资源。"""

    def _create_runner(
        self, km_driver: KmboxDriver, video_capture: VideoCapture
    ) -> BotRunner:
        image_engine = ImageEngine()
        player_action = PlayerActions(km_driver)
        skill_factory = SkillFactory(km_driver)
        role = create_role(player_action, skill_factory)
        state = BotState(role)
        strategy = create_strategy(state)

        return BotRunner(
            state=state,
            video_capture=video_capture,
            image_engine=image_engine,
            player_action=player_action,
            strategy=strategy,
        )

    def run(self) -> None:
        km_driver = KmboxDriver()
        video_capture = None

        try:
            video_capture = VideoCapture()
            runner = self._create_runner(km_driver, video_capture)
            runner.run()
        finally:
            self._close_resources(km_driver, video_capture)

    @staticmethod
    def _close_resources(
        km_driver: KmboxDriver,
        video_capture: VideoCapture | None,
    ) -> None:
        km_driver.close()
        if video_capture is not None:
            video_capture.release()


def main():
    Aion2Bot().run()


if __name__ == "__main__":
    main()
