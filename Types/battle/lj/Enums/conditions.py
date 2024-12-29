from Utilities.util import base_enum, base_enum_int


class ButtonsOE(base_enum):
    Square = 0
    Triangle = 1
    Circle = 2
    Cross = 3
    L1 = 4
    R1 = 5
    R2 = 6
    L2 = 7
    PadUp = 8
    PadDown = 9
    PadLeft = 10
    PadRight = 11
    Unknown5 = 12
    Unknown6 = 13
    Unknown7 = 14
    Unknown8 = 15


class ButtonsDE(base_enum):
    invalid = 0
    Square = 1
    Triangle = 2
    Circle = 3
    Cross = 4
    L1 = 5
    L2 = 6
    R1 = 7
    R2 = 8
    PadUp = 9
    PadDown = 10
    PadLeft = 11
    PadRight = 12
    Unknown5 = 13
    Unknown6 = 14
    L3 = 15


class Status(base_enum_int):
    invalid = 0,
    Heat = 1,
    NotHeat = 2,
    Run = 3,
    Down = 4,
    CanSeize = 5,
    HPPinch = 6,
    DownAo = 7,
    DownUtu = 8,
    HeatZero = 9,
    HeatMax = 10,
    OnStair = 11,
    Heavy = 12,
    Bound = 13,
    WallDamage = 14,
    Piyori = 15,
    FromPocket = 16,
    WallHit = 17,
    Drunk = 18,
    CanRobWeapon = 19,
    SyncFront = 20,
    SyncBack = 21,
    Standup = 22,
    Guard = 23,
    Provoke = 24,
    Bibiri = 25,
    Battle = 26,
    Special = 27,
    Bullet = 28,
    Kamae = 29,
    Knuckles = 30,
    Dash = 31,
    ShakeOff = 32,
    GuardBreak = 33,
    FlyDamage = 34,
    Damage = 35,
    Enemy2 = 36,
    CondFree = 37,
    HPFull = 38,
    Dragon = 39,
    Charged = 40,
    HactGal = 41,
    HeatOrDragon = 42,
    Binbo = 43,
    SyncAction = 44,
    BattleRoyal = 45,
    LaunchDown = 46,
    VRBattle = 47,
    FullDrunk = 48,
    OnCarCollision = 49,
    DrunkLimit = 50,
    Dead = 51,
    AttackGuard = 52,
    Surrender = 53,
    NoDisarm = 54,
    EnableDisarm = 55,
    JustSway = 56,
    JustGuardBreak = 57,
    RecoverDead = 58,
    Agony = 59,
    CanStyleChange = 60,
    Attack = 61,
    NoMaiStyleSeize = 62,
    Air = 63,
    Ragdoll = 64,
    CanPickupHeavy = 65,
    WallBound = 66,
    IsKaito = 67,
    IsYagami = 68,
    NearJun = 69

class Conditionals(base_enum):
    UNK0 = 0
    UNK1 = 1
    UNK2 = 2
    UNK3 = 3
    UNK4 = 4
    UNK5 = 5
    UNK6 = 6
    NOT = 7


class Directions(base_enum):
    Forward = 0
    Left = 1
    Back = 2
    Right = 3
