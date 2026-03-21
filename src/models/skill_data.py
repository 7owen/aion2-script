import kmbox_net

from .metadata import BuffMetadata, SkillMetadata

# ==========================================
# Game Entities (Constants)
# ==========================================

# --- Buffs ---
BAOJI = "baoji"
GEDANG = "gedang"

BIAOBA = "biaoba"
CHIHUAN = "chihuan"
JIDAO = "jidao"
SHUFU = "shufu"
CAN_XIAPANJI = "can_xiapanji"

# --- Common Skills ---
HUIXUE = "huixue"
TIAOYUE = "tiaoyue"
JINJIHUIBI = "jinjihuibi"

# --- Swordstar Skills ---
TIAOYUEGONGJI = "tiaoyuegongji"
ROULINJIAN = "roulinjian"
FENSUIBODONG = "fensuibodong"
POMIEMENGJI = "pomiemengji"
FENNUBODONG = "fennubodong"
QIANGXIYIJI = "qiangxiyiji"
JINUBAOZHA = "jinubaozha"
JIAOHUAIZHAN = "jiaohuaizhan"
RUILIYIJI = "ruiliyiji"
ZHANDUANMENGJI = "zhanduanmengji"
TUJINYIJI = "tujinyiji"
KONGZHONGJIEFU = "kongzhongjiefu"
XIAPANJI = "xiapanji"

# --- Bowstar Skills ---
TAOSUOJIAN = "taosuojian"
FENGKUANGJIAN = "fengkuangjian"
BAOZHAQUANTAO = "baozhaquantao"
MIAOZHUNJIAN = "miaozhunjian"
JIANSHIFENGBAO = "jianshifengbao"
TUJITI = "tujiti"
BAISHENMEGUANNENG = "baishenmeguanneng"
BAOZHAJIAN = "baozhajian"
LIZHUIJIAN = "lizhuijian"
POLIEJIAN = "poliejian"
MUBIAOJIAN = "mubiaojian"
YAZHIJIAN = "yazhijian"
JUJI = "juji"
SUSHE = "sushe"


# ==========================================
# Registries (For Factory / Lookups)
# ==========================================


TARGET_BUFFS = {
    BIAOBA: BuffMetadata(BIAOBA, "标靶状态", 10),
    CHIHUAN: BuffMetadata(CHIHUAN, "迟缓状态", 5),
    JIDAO: BuffMetadata(JIDAO, "击倒状态", 5),
    SHUFU: BuffMetadata(SHUFU, "束缚", 5),
    CAN_XIAPANJI: BuffMetadata(CAN_XIAPANJI, "可释放下盘击状态", 10),
}


SWORDSTAR_BUFFS = {
    GEDANG: BuffMetadata(GEDANG, "格挡状态", 5),
}

BOWSTAR_BUFFS = {
    BAOJI: BuffMetadata(BAOJI, "暴击状态", 3),
}


COMMON_SKILLS = {
    HUIXUE: SkillMetadata(HUIXUE, "回血", kmbox_net.KEY_F1, cooldown=15),
    TIAOYUE: SkillMetadata(TIAOYUE, "跳跃", kmbox_net.KEY_SPACEBAR),
    JINJIHUIBI: SkillMetadata(
        JINJIHUIBI, "紧急回避", kmbox_net.KEY_LEFTSHIFT, cooldown=1
    ),
}

SWORDSTAR_SKILLS = {
    TIAOYUEGONGJI: SkillMetadata(
        TIAOYUEGONGJI, "跳跃攻击", kmbox_net.KEY_1, cooldown=16
    ),
    ROULINJIAN: SkillMetadata(
        ROULINJIAN,
        "蹂躏剑",
        kmbox_net.KEY_2,
        cooldown=21,
        max_range=4,
        time_consumption=1.5,
        generate_buff_codes=[JIDAO],
    ),
    FENSUIBODONG: SkillMetadata(
        FENSUIBODONG,
        "粉碎波动",
        kmbox_net.KEY_3,
        cooldown=21,
        max_range=4,
        time_consumption=1.5,
        press_count=2,
    ),
    POMIEMENGJI: SkillMetadata(POMIEMENGJI, "破灭猛击", kmbox_net.KEY_4, cooldown=30),
    FENNUBODONG: SkillMetadata(
        FENNUBODONG,
        "愤怒波动",
        kmbox_net.KEY_5,
        cooldown=61,
        max_range=4,
        time_consumption=1,
        generate_buff_codes=[JIDAO],
    ),
    QIANGXIYIJI: SkillMetadata(
        QIANGXIYIJI,
        "强袭一击",
        kmbox_net.KEY_6,
        cooldown=121,
        time_consumption=1,
        generate_buff_codes=[JIDAO],
    ),
    JINUBAOZHA: SkillMetadata(
        JINUBAOZHA,
        "激怒爆炸",
        kmbox_net.KEY_7,
        cooldown=46,
        max_range=4,
        time_consumption=1,
        generate_buff_codes=[CAN_XIAPANJI],
    ),
    JIAOHUAIZHAN: SkillMetadata(
        JIAOHUAIZHAN,
        "脚踝斩",
        kmbox_net.KEY_E,
        cooldown=11,
        max_range=4,
        generate_buff_codes=[JIDAO],
        require_buff_codes=[GEDANG],
    ),
    RUILIYIJI: SkillMetadata(RUILIYIJI, "锐利一击", kmbox_net.KEY_R),
    ZHANDUANMENGJI: SkillMetadata(
        ZHANDUANMENGJI, "斩断猛击", kmbox_net.KEY_T, max_range=4
    ),
    TUJINYIJI: SkillMetadata(
        TUJINYIJI,
        "突进一击",
        kmbox_net.KEY_Q,
        cooldown=21,
        max_range=4,
        generate_buff_codes=[JIDAO],
    ),
    KONGZHONGJIEFU: SkillMetadata(
        KONGZHONGJIEFU,
        "空中结缚",
        kmbox_net.KEY_Q,
        cooldown=46,
        max_range=4,
        time_consumption=1.5,
        require_buff_codes=[JIDAO],
    ),
    XIAPANJI: SkillMetadata(
        XIAPANJI,
        "下盘击",
        kmbox_net.KEY_E,
        cooldown=6,
        max_range=4,
        time_consumption=1.5,
        press_count=2,
        require_buff_codes=[JIDAO, CAN_XIAPANJI],
    ),
}

BOWSTAR_SKILLS = {
    TAOSUOJIAN: SkillMetadata(
        TAOSUOJIAN,
        "套索箭",
        kmbox_net.KEY_1,
        cooldown=16,
        generate_buff_codes=[CHIHUAN],
    ),
    FENGKUANGJIAN: SkillMetadata(
        FENGKUANGJIAN,
        "疯狂箭",
        kmbox_net.KEY_2,
        cooldown=21,
        max_range=20,
        press_holdon=0.5,
    ),
    BAOZHAQUANTAO: SkillMetadata(
        BAOZHAQUANTAO,
        "爆炸圈套",
        kmbox_net.KEY_3,
        cooldown=21,
        max_range=20,
        generate_buff_codes=[SHUFU],
    ),
    MIAOZHUNJIAN: SkillMetadata(
        MIAOZHUNJIAN,
        "瞄准箭",
        kmbox_net.KEY_4,
        cooldown=21,
        max_range=20,
        press_holdon=1.5,
        require_buff_codes=[BIAOBA],
    ),
    JIANSHIFENGBAO: SkillMetadata(
        JIANSHIFENGBAO,
        "箭失风暴",
        kmbox_net.KEY_5,
        cooldown=61,
        generate_buff_codes=[CHIHUAN],
    ),
    TUJITI: SkillMetadata(TUJITI, "突击踢", kmbox_net.KEY_6, cooldown=30, max_range=5),
    BAISHENMEGUANNENG: SkillMetadata(
        BAISHENMEGUANNENG, "白什么灌能", kmbox_net.KEY_7, cooldown=61
    ),
    BAOZHAJIAN: SkillMetadata(
        BAOZHAJIAN, "爆炸箭", kmbox_net.KEY_8, cooldown=46, max_range=20
    ),
    LIZHUIJIAN: SkillMetadata(
        LIZHUIJIAN,
        "利锥箭",
        kmbox_net.KEY_Q,
        cooldown=5,
        max_range=20,
        require_buff_codes=[BAOJI],
    ),
    POLIEJIAN: SkillMetadata(
        POLIEJIAN,
        "破裂箭",
        kmbox_net.KEY_Q,
        cooldown=31,
        max_range=20,
        require_buff_codes=[CHIHUAN, SHUFU],
    ),
    MUBIAOJIAN: SkillMetadata(
        MUBIAOJIAN,
        "目标箭",
        kmbox_net.KEY_E,
        cooldown=11,
        max_range=20,
        generate_buff_codes=[BIAOBA],
    ),
    YAZHIJIAN: SkillMetadata(
        YAZHIJIAN,
        "压制箭",
        kmbox_net.KEY_E,
        cooldown=21,
        max_range=20,
        require_buff_codes=[BIAOBA],
    ),
    JUJI: SkillMetadata(JUJI, "狙击", kmbox_net.KEY_R),
    SUSHE: SkillMetadata(SUSHE, "速射", kmbox_net.KEY_T, max_range=20),
}
