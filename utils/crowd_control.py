from datetime import datetime
import os
import random

# triggers on exact amounts of bits cheered
pm64_bit_values = {
    5:      "Set FP Max",
    10:     "Set HP Max",
    12:     "Add 10 Coins",
    16:     "Subtract 10 Coins",
    20:     "Set HP 1",
    25:     "Set HP 2",
    40:     "Berserker",            # 1 minute
    50:     "Random Pitch",         # 1 minute
    55:     "Set FP 0",
    69:     "Toggle Mirror Mode",
    75:     "Shuffle Current Seed", # change seed being played
    80:     "Disable Speedy Spin",  # 1 minute
    100:    "Slow Go",              # 1 minute
    200:    "Disable All Badges",
    220:    "Disable Heart Blocks", # 5 minutes
    250:    "Disable Save Blocks",  # 5 minutes
    300:    "Homeward Shroom",
    500:    "Interval Swap",        # change seed 10 times in 10 second intervals
    1000:   "Set Homeward Shroom"
}

# triggers on exact amounts of gift subs
pm64_sub_values = {
    1:  "Slow Go",          # 90 seconds
    5:  "OHKO Mode",        # 5-10 minutes (random)
    10: "Interval Swap",    # change seed 30 times in 10 second intervals
    50: "Poverty"           # 1hp, 0fp, 0 coins, 
                            # disable heart blocks for 10 minutes, 
                            # disable save blocks for 10 minutes, 
                            # slow go for 10 minutes, 
                            # ohko 10 minutes
}

cc_root = "./commands/resources/crowdcontrol"
cc_multiplier = int(os.environ.get("CC_MULTIPLIER", "1"))
slowgo_queue        = 0
berserker_queue     = 0
random_pitch_queue  = 0
speedy_queue        = 0
heart_block_queue   = 0
save_block_queue    = 0
ohko_queue          = 0
interval_swaps      = 0

def set_cc_multiplier(mult: int):
    global cc_multiplier
    if mult != 0:
        cc_multiplier = mult

def handle_pm64_cc_subs(subcnt):
    global slowgo_queue
    global berserker_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue
    global interval_swaps

    if subcnt in pm64_sub_values:
        if pm64_sub_values[subcnt] == "Slow Go":
            slowgo_queue += 90
            print(f"[CC {datetime.now()}] Slow Go {slowgo_queue} seconds")
            with open(f"{cc_root}/pm64r-slowgo.txt", "w+") as f:
                f.write("YEP")
        elif pm64_sub_values[subcnt] == "OHKO Mode":
            ohko_queue += random.randint(300, 600)
            print(f"[CC {datetime.now()}] OHKO Mode {ohko_queue}")
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")
        elif pm64_sub_values[subcnt] == "Interval Swap":
            interval_swaps += 29 # 30 including the current one
            print(f"[CC {datetime.now()}] Adding Interval Swaps {interval_swaps}")
            with open(f"{cc_root}/pm64r-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_sub_values[subcnt] == "Poverty":
            print(f"[CC {datetime.now()}] POVERTY")
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
    global cc_multiplier
    global slowgo_queue
    global berserker_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue
    global interval_swaps

    bits //= cc_multiplier
    if bits in pm64_bit_values:
        if pm64_bit_values[bits] == "Set FP Max":
            print(f"[CC {datetime.now()}] Set FP Max")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("99")
        elif pm64_bit_values[bits] == "Set FP 0":
            print(f"[CC {datetime.now()}] Set FP 0")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("0")
        elif pm64_bit_values[bits] == "Set HP Max":
            print(f"[CC {datetime.now()}] Set HP Max")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("99")
        elif pm64_bit_values[bits] == "Set HP 1":
            print(f"[CC {datetime.now()}] Set HP 1")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("1")
        elif pm64_bit_values[bits] == "Set HP 2":
            print(f"[CC {datetime.now()}] Set HP 2")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("2")
        elif pm64_bit_values[bits] == "Add 10 Coins":
            print(f"[CC {datetime.now()}] Add 10 Coins")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("10")
        elif pm64_bit_values[bits] == "Subtract 10 Coins":
            print(f"[CC {datetime.now()}] Subtract 10 Coins")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("-10")
        elif pm64_bit_values[bits] == "Berserker":
            berserker_file = f"{cc_root}/pm64r-berserker.txt"
            berserker_queue += 60
            if not(os.path.isfile(berserker_file)):
                print(f"[CC {datetime.now()}] Berserker {berserker_queue} seconds")
                with open(berserker_file, "w+") as f:
                    f.write("who?")
        elif pm64_bit_values[bits] == "Slow Go":
            slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
            slowgo_queue += 60
            if not(os.path.isfile(slowgo_file)):
                print(f"[CC {datetime.now()}] Slow Go {slowgo_queue} seconds")
                with open(slowgo_file, "w+") as f:
                    f.write("Of course")
        elif pm64_bit_values[bits] == "Random Pitch":
            pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
            random_pitch_queue += 60
            if not(os.path.isfile(pitch_file)):
                print(f"[CC {datetime.now()}] Random Pitch enabled")
                with open(pitch_file, "w+") as f:
                    f.write("why??")
        elif pm64_bit_values[bits] == "Disable All Badges":
            print(f"[CC {datetime.now()}] Disable All Badges")
            with open(f"{cc_root}/pm64r-disablebadges.txt", "w+") as f:
                f.write("Rude af")
        elif pm64_bit_values[bits] == "Shuffle Current Seed":
            print(f"[CC {datetime.now()}] Shuffle Current Seed")
            with open(f"{cc_root}/pm64r-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_bit_values[bits] == "Interval Swap":
            interval_swaps += 9 # 10 including the current one
            print(f"[CC {datetime.now()}] Adding Interval Swaps {interval_swaps}")
            with open(f"{cc_root}/pm64r-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_bit_values[bits] == "Toggle Mirror Mode":
            print(f"[CC {datetime.now()}] Toggle Mirror Mode")
            with open(f"{cc_root}/pm64r-toggle-mirror.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Speedy Spin":
            print(f"[CC {datetime.now()}] Disable Speedy Spin")
            speedy_queue += 60
            with open(f"{cc_root}/pm64r-disable-speedy.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Heart Blocks":
            print(f"[CC {datetime.now()}] Disable Heart Blocks")
            heart_block_queue += 300
            with open(f"{cc_root}/pm64r-disable-heart-blocks.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Save Blocks":
            print(f"[CC {datetime.now()}] Disable Save Blocks")
            save_block_queue += 300
            with open(f"{cc_root}/pm64r-disable-save-blocks.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "OHKO Mode":
            ohko_queue += 300
            print(f"[CC {datetime.now()}] OHKO Mode {ohko_queue}")
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Homeward Shroom":
            print(f"[CC {datetime.now()}] Homeward Shroom")
            with open(f"{cc_root}/pm64r-homeward-shroom.txt", "w+") as f:
                f.write("god dammit")
        elif pm64_bit_values[bits] == "Set Homeward Shroom":
            print(f"[CC {datetime.now()}] Set Homeward Shroom")
            with open(f"{cc_root}/pm64r-set-homeward-shroom.txt", "w+") as f:
                f.write("oh no")

def handle_pm64_cc_periodic_update(seconds):
    global slowgo_queue
    global berserker_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue
    global interval_swaps

    update_time = lambda a : max(a - seconds, 0)

    slowgo_queue = update_time(slowgo_queue)
    berserker_queue = update_time(berserker_queue)
    random_pitch_queue = update_time(random_pitch_queue)
    speedy_queue = update_time(speedy_queue)
    heart_block_queue = update_time(heart_block_queue)
    save_block_queue = update_time(save_block_queue)
    ohko_queue = update_time(ohko_queue)

    slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
    berserker_file = f"{cc_root}/pm64r-berserker.txt"
    pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
    speedy_file = f"{cc_root}/pm64r-disable-speedy.txt"
    heart_block_file = f"{cc_root}/pm64r-disable-heart-blocks.txt"
    save_block_file = f"{cc_root}/pm64r-disable-save-blocks.txt"
    ohko_file = f"{cc_root}/pm64r-ohko.txt"

    if slowgo_queue <= 0 and os.path.isfile(slowgo_file):
        print(f"[CC {datetime.now()}] Slow Go no longer enabled")
        os.remove(slowgo_file)

    if berserker_queue <= 0 and os.path.isfile(berserker_file):
        print(f"[CC {datetime.now()}] Berserker no longer enabled")
        os.remove(berserker_file)

    if random_pitch_queue <= 0 and os.path.isfile(pitch_file):
        print(f"[CC {datetime.now()}] Random Pitch no longer enabled")
        os.remove(pitch_file)

    if speedy_queue <= 0 and os.path.isfile(speedy_file):
        print(f"[CC {datetime.now()}] Speedy Spin is no longer disabled")
        os.remove(speedy_file)

    if heart_block_queue <= 0 and os.path.isfile(heart_block_file):
        print(f"[CC {datetime.now()}] Heart Blocks no longer disabled")
        os.remove(heart_block_file)

    if save_block_queue <= 0 and os.path.isfile(save_block_file):
        print(f"[CC {datetime.now()}] Save Blocks no longer disabled")
        os.remove(save_block_file)

    if ohko_queue <= 0 and os.path.isfile(ohko_file):
        print(f"[CC {datetime.now()}] OHKO Mode no longer enabled")
        os.remove(ohko_file)

    if interval_swaps > 0:
        with open(f"{cc_root}/pm64r-shuffle.txt", "w+") as f:
            f.write("Shuffle")
        interval_swaps -= 1

