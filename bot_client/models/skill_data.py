import kmbox_net

from .metadata import BuffMetadata, SkillMetadata

# ==========================================
# Game Entities (Constants)
# ==========================================

# --- Buffs ---
BUFF_BAOJI = "baoji"
BUFF_GEDANG = "gedang"

BUFF_BIAOBA = "biaoba"
BUFF_CHIHUAN = "chihuan"
BUFF_JIDAO = "jidao"
BUFF_SHUFU = "shufu"
BUFF_CAN_XIAPANJI = "can_xiapanji"

# --- Common Skills ---
SKILL_HUIXUE = "huixue"
SKILL_TIAOYUE = "tiaoyue"
SKILL_JINJIHUIBI = "jinjihuibi"

# --- Swordstar Skills ---
SKILL_TIAOYUEGONGJI = "tiaoyuegongji"
SKILL_ROULINJIAN = "roulinjian"
SKILL_FENSUIBODONG = "fensuibodong"
SKILL_POMIEMENGJI = "pomiemengji"
SKILL_FENNUBODONG = "fennubodong"
SKILL_QIANGXIYIJI = "qiangxiyiji"
SKILL_JINUBAOZHA = "jinubaozha"
SKILL_JIAOHUAIZHAN = "jiaohuaizhan"
SKILL_RUILIYIJI = "ruiliyiji"
SKILL_ZHANDUANMENGJI = "zhanduanmengji"
SKILL_TUJINYIJI = "tujinyiji"
SKILL_KONGZHONGJIEFU = "kongzhongjiefu"
SKILL_XIAPANJI = "xiapanji"

# --- Bowstar Skills ---
SKILL_TAOSUOJIAN = "taosuojian"
SKILL_FENGKUANGJIAN = "fengkuangjian"
SKILL_BAOZHAQUANTAO = "baozhaquantao"
SKILL_MIAOZHUNJIAN = "miaozhunjian"
SKILL_JIANSHIFENGBAO = "jianshifengbao"
SKILL_TUJITI = "tujiti"
SKILL_BAISHENMEGUANNENG = "baishenmeguanneng"
SKILL_BAOZHAJIAN = "baozhajian"
SKILL_LIZHUIJIAN = "lizhuijian"
SKILL_POLIEJIAN = "poliejian"
SKILL_MUBIAOJIAN = "mubiaojian"
SKILL_YAZHIJIAN = "yazhijian"
SKILL_JUJI = "juji"
SKILL_SUSHE = "sushe"


# ==========================================
# Registries (For Factory / Lookups)
# ==========================================


TARGET_BUFFS = []

ROLE_BUFFS = [
    BuffMetadata(BUFF_JIDAO, "击倒状态", 5),
    BuffMetadata(BUFF_SHUFU, "束缚", 5),
    BuffMetadata(BUFF_CAN_XIAPANJI, "可释放下盘击状态", 10),
    BuffMetadata(BUFF_CHIHUAN, "迟缓状态", 5),
    BuffMetadata(BUFF_BIAOBA, "标靶状态", 10),
    BuffMetadata(BUFF_BAOJI, "暴击状态", 3),
    BuffMetadata(BUFF_GEDANG, "格挡状态", 5),
]

COMMON_SKILLS = [
    SkillMetadata(SKILL_HUIXUE, "回血", kmbox_net.KEY_F1, cooldown=16),
    SkillMetadata(
        SKILL_TIAOYUE,
        "跳跃",
        kmbox_net.KEY_SPACEBAR,
        time_consumption=1.5,
        cooldown=1,
    ),
    SkillMetadata(
        SKILL_JINJIHUIBI,
        "紧急回避",
        kmbox_net.KEY_LEFTSHIFT,
        cooldown=2,
        # time_consumption=1,
    ),
]

SWORDSTAR_SKILLS = [
    SkillMetadata(
        SKILL_TIAOYUEGONGJI,
        "跳跃攻击",
        kmbox_net.KEY_1,
        time_consumption=0.5,
        cooldown=16,
        min_range=6,
        max_range=20,
    ),
    SkillMetadata(
        SKILL_ROULINJIAN,
        "蹂躏剑",
        kmbox_net.KEY_2,
        cooldown=21,
        max_range=4,
        time_consumption=1.8,
        generate_buff_codes=[BUFF_JIDAO],
    ),
    SkillMetadata(
        SKILL_FENSUIBODONG,
        "粉碎波动",
        kmbox_net.KEY_3,
        cooldown=21,
        max_range=4,
        time_consumption=2,
        press_count=2,
    ),
    SkillMetadata(
        SKILL_POMIEMENGJI,
        "破灭猛击",
        kmbox_net.KEY_4,
        cooldown=31,
        min_range=6,
        max_range=20,
        time_consumption=1.5,
    ),
    SkillMetadata(
        SKILL_FENNUBODONG,
        "愤怒波动",
        kmbox_net.KEY_5,
        cooldown=61,
        max_range=4,
        time_consumption=1,
        generate_buff_codes=[BUFF_JIDAO],
    ),
    SkillMetadata(
        SKILL_QIANGXIYIJI,
        "强袭一击",
        kmbox_net.KEY_6,
        cooldown=121,
        min_range=6,
        max_range=20,
        time_consumption=1.5,
        generate_buff_codes=[BUFF_JIDAO],
    ),
    SkillMetadata(
        SKILL_JINUBAOZHA,
        "激怒爆炸",
        kmbox_net.KEY_7,
        cooldown=46,
        max_range=4,
        time_consumption=2,
        generate_buff_codes=[BUFF_CAN_XIAPANJI],
    ),
    SkillMetadata(
        SKILL_JIAOHUAIZHAN,
        "脚踝斩",
        kmbox_net.KEY_E,
        cooldown=11,
        max_range=4,
        time_consumption=2,
        press_count=2,
        generate_buff_codes=[BUFF_JIDAO],
        require_buff_codes=[BUFF_GEDANG],
    ),
    SkillMetadata(SKILL_RUILIYIJI, "锐利一击", kmbox_net.KEY_R),
    SkillMetadata(SKILL_ZHANDUANMENGJI, "斩断猛击", kmbox_net.KEY_T, max_range=4),
    SkillMetadata(
        SKILL_TUJINYIJI,
        "突进一击",
        kmbox_net.KEY_Q,
        cooldown=21,
        max_range=16,
        time_consumption=0.5,
        generate_buff_codes=[BUFF_JIDAO],
    ),
    SkillMetadata(
        SKILL_KONGZHONGJIEFU,
        "空中结缚",
        kmbox_net.KEY_Q,
        cooldown=46,
        max_range=4,
        time_consumption=1,
        require_buff_codes=[BUFF_JIDAO],
        anti_swallow=True,
    ),
    SkillMetadata(
        SKILL_XIAPANJI,
        "下盘击",
        kmbox_net.KEY_E,
        cooldown=5.5,
        max_range=4,
        time_consumption=0.8,
        # press_count=2,
        require_buff_codes=[BUFF_JIDAO, BUFF_CAN_XIAPANJI],
    ),
]

BOWSTAR_SKILLS = [
    SkillMetadata(
        SKILL_TAOSUOJIAN,
        "套索箭",
        kmbox_net.KEY_1,
        cooldown=16,
        time_consumption=1.5,
        generate_buff_codes=[BUFF_CHIHUAN],
    ),
    SkillMetadata(
        SKILL_FENGKUANGJIAN,
        "疯狂箭",
        kmbox_net.KEY_2,
        cooldown=21,
        max_range=20,
        time_consumption=0.5,
        press_holdon=0.5,
    ),
    SkillMetadata(
        SKILL_BAOZHAQUANTAO,
        "爆炸圈套",
        kmbox_net.KEY_3,
        time_consumption=0.5,
        cooldown=21,
    ),
    SkillMetadata(
        SKILL_MIAOZHUNJIAN,
        "瞄准箭",
        kmbox_net.KEY_4,
        cooldown=21,
        max_range=20,
        time_consumption=2,
        press_holdon=1.5,
        require_buff_codes=[BUFF_BIAOBA],
    ),
    SkillMetadata(
        SKILL_JIANSHIFENGBAO,
        "箭失风暴",
        kmbox_net.KEY_5,
        cooldown=61,
        time_consumption=1.5,
        generate_buff_codes=[BUFF_CHIHUAN],
    ),
    SkillMetadata(
        SKILL_TUJITI,
        "突击踢",
        kmbox_net.KEY_6,
        cooldown=31,
        max_range=5,
        time_consumption=2,
    ),
    SkillMetadata(SKILL_BAISHENMEGUANNENG, "白什么灌能", kmbox_net.KEY_7, cooldown=61),
    SkillMetadata(
        SKILL_BAOZHAJIAN,
        "爆炸箭",
        kmbox_net.KEY_8,
        cooldown=46,
        time_consumption=0.5,
        max_range=20,
    ),
    SkillMetadata(
        SKILL_LIZHUIJIAN,
        "利锥箭",
        kmbox_net.KEY_Q,
        cooldown=5.5,
        time_consumption=0.5,
        max_range=20,
        require_buff_codes=[BUFF_BAOJI],
        anti_swallow=True,
    ),
    SkillMetadata(
        SKILL_POLIEJIAN,
        "破裂箭",
        kmbox_net.KEY_Q,
        cooldown=31,
        time_consumption=0.5,
        max_range=20,
        require_buff_codes=[BUFF_CHIHUAN],
    ),
    SkillMetadata(
        SKILL_MUBIAOJIAN,
        "目标箭",
        kmbox_net.KEY_E,
        cooldown=11,
        max_range=20,
        time_consumption=1,
        generate_buff_codes=[BUFF_BIAOBA],
    ),
    SkillMetadata(
        SKILL_YAZHIJIAN,
        "压制箭",
        kmbox_net.KEY_E,
        cooldown=21,
        time_consumption=0.5,
        max_range=20,
        require_buff_codes=[BUFF_BIAOBA],
    ),
    SkillMetadata(SKILL_JUJI, "狙击", kmbox_net.KEY_R),
    SkillMetadata(SKILL_SUSHE, "速射", kmbox_net.KEY_T, max_range=20),
]
