from bot_config import BotConfig
from bot_runner import BotRunner
from factories import create_role, create_strategy
from game_context import BotState
from image_engine import ImageEngine
from km_driver import KmboxDriver
from player_actions import PlayerActions
from skill_factory import SkillFactory
from video_capture import VideoCapture


class Aion2Bot:
    """组合应用依赖，并管理运行期资源。"""

    def __init__(self, config: BotConfig | None = None):
        self.config = config or BotConfig()

    def _create_runner(
        self, km_driver: KmboxDriver, video_capture: VideoCapture
    ) -> BotRunner:
        image_engine = ImageEngine(config=self.config)
        state = BotState(self.config.role.extract_interval_seconds)
        player_action = PlayerActions(km_driver)
        skill_factory = SkillFactory(km_driver)
        role = create_role(self.config, player_action, skill_factory, state)
        strategy = create_strategy(self.config, state)

        return BotRunner(
            state=state,
            video_capture=video_capture,
            image_engine=image_engine,
            player_action=player_action,
            role=role,
            strategy=strategy,
            max_ops_per_second=self.config.runtime.max_ops_per_second,
        )

    def run(self) -> None:
        km_driver = KmboxDriver(config=self.config.kmbox)
        video_capture = None

        try:
            video_capture = VideoCapture(config=self.config.video)
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
