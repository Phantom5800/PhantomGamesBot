import os
import random

pm64_bit_values = {
    5:      "Set FP Max",
    10:     "Set HP Max",
    12:     "Add 10 Coins",
    16:     "Subtract 10 Coins",
    20:     "Set HP 1",
    25:     "Set HP 2",
    50:     "Random Pitch",         # 1 minute
    55:     "Set FP 0",
    60:     "Toggle Mirror Mode",
    75:     "Shuffle Current Seed", # change seed being played
    80:     "Disable Speedy Spin",  # 1 minute
    100:    "Slow Go",              # 1 minute
    200:    "Disable All Badges",
    220:    "Disable Heart Blocks", # 5 minutes
    250:    "Disable Save Blocks",  # 5 minutes
    1000:   "OHKO Mode"             # 5 minutes
}

pm64_sub_values = {
    1:  "Slow Go",      # 90 seconds
    5:  "OHKO Mode",    # 5-10 minutes (random)
    50: "Poverty"       # 1hp, 0fp, 0 coins, 
                        # disable heart blocks for 10 minutes, 
                        # disable save blocks for 10 minutes, 
                        # slow go for 10 minutes, 
                        # ohko 10 minutes
}

cc_root = "./commands/resources/crowdcontrol"
cc_multiplier = int(os.environ.get("CC_MULTIPLIER", "1"))
slowgo_queue        = 0
random_pitch_queue  = 0
speedy_queue        = 0
heart_block_queue   = 0
save_block_queue    = 0
ohko_queue          = 0

def set_cc_multiplier(mult: int):
    if mult != 0:
        cc_multiplier = mult

def handle_pm64_cc_subs(subcnt):
    if subcnt in pm64_sub_values:
        if pm64_sub_values[subcnt] == "Slow Go":
            print("[CC] Slow Go")
            slowgo_queue += 90
            with open(f"{cc_root}/pm64r-slowgo.txt", "w+") as f:
                f.write("YEP")
        elif pm64_sub_values[subcnt] == "OHKO Mode":
            print("[CC] OHKO Mode")
            ohko_queue += random.randint(300, 600)
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")
        elif pm64_sub_values[subcnt] == "Poverty":
            print("[CC] POVERTY")
            ohko_queue += 600
            slowgo_queue += 600
            heart_block_queue += 600
            save_block_queue += 600
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("1")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("0")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("-999")
            with open(f"{cc_root}/pm64r-disable-heart-blocks.txt", "w+") as f:
                f.write("eww")
            with open(f"{cc_root}/pm64r-disable-save-blocks.txt", "w+") as f:
                f.write("eww")
            with open(f"{cc_root}/pm64r-slowgo.txt", "w+") as f:
                f.write("eww")
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")

def handle_pm64_cc_bits(bits):
    global slowgo_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue

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
            slowgo_queue += 60
            if not(os.path.isfile(slowgo_file)):
                print("[CC] Slow Go enabled")
                with open(slowgo_file, "w+") as f:
                    f.write("Of course")
        elif pm64_bit_values[bits] == "Random Pitch":
            pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
            random_pitch_queue += 60
            if not(os.path.isfile(pitch_file)):
                print("[CC] Random Pitch enabled")
                with open(pitch_file, "w+") as f:
                    f.write("why??")
        elif pm64_bit_values[bits] == "Disable All Badges":
            print("[CC] Disable All Badges")
            with open(f"{cc_root}/pm64r-disablebadges.txt", "w+") as f:
                f.write("Rude af")
        elif pm64_bit_values[bits] == "Shuffle Current Seed":
            print("[CC] Shuffle Current Seed")
            with open(f"{cc_root}/pm64r-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_bit_values[bits] == "Toggle Mirror Mode":
            print("[CC] Toggle Mirror Mode")
            with open(f"{cc_root}/pm64r-toggle-mirror.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Speedy Spin":
            print("[CC] Disable Speedy Spin")
            speedy_queue += 60
            with open(f"{cc_root}/pm64r-disable-speedy.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Heart Blocks":
            print("[CC] Disable Heart Blocks")
            heart_block_queue += 300
            with open(f"{cc_root}/pm64r-disable-heart-blocks.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Save Blocks":
            print("[CC] Disable Save Blocks")
            save_block_queue += 300
            with open(f"{cc_root}/pm64r-disable-save-blocks.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "OHKO Mode":
            print("[CC] OHKO Mode")
            ohko_queue += 300
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")

def handle_pm64_cc_periodic_update(seconds):
    global slowgo_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue

    update_time = lambda a : max(a - seconds, 0)

    slowgo_queue = update_time(slowgo_queue)
    random_pitch_queue = update_time(random_pitch_queue)
    speedy_queue = update_time(speedy_queue)
    heart_block_queue = update_time(heart_block_queue)
    save_block_queue = update_time(save_block_queue)
    ohko_queue = update_time(ohko_queue)

    slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
    pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
    speedy_file = f"{cc_root}/pm64r-disable-speedy.txt"
    heart_block_file = f"{cc_root}/pm64r-disable-heart-blocks.txt"
    save_block_file = f"{cc_root}/pm64r-disable-save-blocks.txt"
    ohko_file = f"{cc_root}/pm64r-ohko.txt"

    if slowgo_queue <= 0 and os.path.isfile(slowgo_file):
        print("[CC] Slow Go no longer enabled")
        os.remove(slowgo_file)

    if random_pitch_queue <= 0 and os.path.isfile(pitch_file):
        print("[CC] Random Pitch no longer enabled")
        os.remove(pitch_file)

    if speedy_queue <= 0 and os.path.isfile(speedy_file):
        print("[CC] Speedy Spin is no longer disabled")
        os.remove(speedy_file)

    if heart_block_queue <= 0 and os.path.isfile(heart_block_file):
        print("[CC] Heart Blocks no longer disabled")
        os.remove(heart_block_file)

    if save_block_queue <= 0 and os.path.isfile(save_block_file):
        print("[CC] Save Blocks no longer disabled")
        os.remove(save_block_file)

    if ohko_queue <= 0 and os.path.isfile(ohko_file):
        print("[CC] OHKO Mode no longer enabled")
        os.remove(ohko_file)
