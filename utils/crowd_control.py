import os

pm64_bit_values = {
    5:      "Set FP Max",
    10:     "Set HP Max",
    12:     "Add 10 Coins",
    16:     "Subtract 10 Coins",
    20:     "Set HP 1",
    25:     "Set HP 2",
    50:     "Random Pitch"
    55:     "Set FP 0",
    100:    "Slow Go",
    200:    "Disable All Badges"
}

cc_root = "./commands/resources/crowdcontrol"
cc_multiplier = int(os.environ.get("CC_MULTIPLIER", "1"))
slowgo_queue = 0
random_pitch_queue = 0

def set_cc_multiplier(mult: int):
    if mult != 0:
        cc_multiplier = mult

def handle_pm64_cc_bits(bits):
    bits //= cc_multiplier
    if bits in pm64_bit_values:
        if pm64_bit_values[bits] == "Set FP Max":
            print("[CC] Set FP Max")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("99")
        elif pm64_bit_values[bits] == "Set FP 0":
            print("[CC] Set FP 0")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("0")
        elif pm64_bit_values[bits] == "Set HP Max":
            print("[CC] Set HP Max")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("99")
        elif pm64_bit_values[bits] == "Set HP 1":
            print("[CC] Set HP 1")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("1")
        elif pm64_bit_values[bits] == "Set HP 2":
            print("[CC] Set HP 2")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("2")
        elif pm64_bit_values[bits] == "Add 10 Coins":
            print("[CC] Add 10 Coins")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("10")
        elif pm64_bit_values[bits] == "Subtract 10 Coins":
            print("[CC] Subtract 10 Coins")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("-10")
        elif pm64_bit_values[bits] == "Slow Go":
            slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
            if not(os.path.isfile(slowgo_file)):
                print("[CC] Slow Go enabled")
                with open(slowgo_file, "w+") as f:
                    f.write("Of course")
            slowgo_queue += 60
        elif pm64_bit_values[bits] == "Random Pitch":
            pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
            if not(os.path.isfile(slowgo_file)):
                print("[CC] Random Pitch enabled")
                with open(pitch_file, "w+") as f:
                    f.write("why??")
            random_pitch_queue += 60
        elif pm64_bit_values[bits] == "Disable All Badges":
            print("[CC] Disable All Badges")
            with open(f"{cc_root}/pm64r-disablebadges.txt", "w+") as f:
                f.write("Rude af")

def handle_pm64_cc_periodic_update(seconds):
    slowgo_queue = max(slowgo_queue - seconds, 0)
    random_pitch_queue = max(random_pitch_queue - seconds, 0)

    slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
    pitch_file = f"{cc_root}/pm64r-random-pitch.txt"

    if slowgo_queue <= 0 and os.path.isfile(slowgo_file):
        print("[CC] Slow Go no longer enabled")
        os.remove(slowgo_file)

    if random_pitch_queue <= 0 and os.path.isfile(pitch_file):
        print("[CC] Random Pitch no longer enabled")
        os.remove(pitch_file)
