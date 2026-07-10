import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
TOKEN = '8777718464:AAHU9yDQviSt5vFsZTqUQU12oVsCIV0SNeY'
CHAT_ID = '-1002408035440'
API_URL = 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'

ist = pytz.timezone('Asia/Kolkata')

# --- SYSTEM SETTINGS ---
config_state = {
    "SYSTEM_MODE": "IN_TIME",  # Default mode: IN_TIME
    "is_session_active": False,
    "last_prediction_data": None,
    "last_minute_triggered": ""
}

# --- TRACKING ---
stats = {"wins": 0, "losses": 0, "max_win_streak": 0, "max_loss_streak": 0, "curr_streak": 0}

def get_log_time():
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

def get_session_schedule():
    now = datetime.now(ist)
    h, m = now.hour, now.minute
    slots = [
        (7, 0, 7, 15, "07:00 AM"),
        (9, 0, 9, 15, "09:00 AM"),
        (21, 0, 21, 15, "09:00 PM")
    ]
    current = None
    next_s = "07:00 AM (Tomorrow)"
    for s_h, s_m, e_h, e_m, label in slots:
        if (s_h, s_m) <= (h, m) < (e_h, e_m):
            current = label
        elif (h, m) < (s_h, s_m) and next_s == "07:00 AM (Tomorrow)":
            next_s = label
    return current, next_s

# --- HTTP TELEGRAM METHODS ---
def send_tg_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[{get_log_time()}] ⚠️ [TG SEND ERROR] {e}", flush=True)

def send_admin_panel(target_chat_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        reply_markup = {
            "inline_keyboard": [
                [{"text": "⏰ IN TIME (Scheduled Slots)", "callback_data": "mode_intime"}],
                [{"text": "🔄 EVERY TIME (24/7 Continuous)", "callback_data": "mode_everytime"}]
            ]
        }
        payload = {
            "chat_id": target_chat_id,
            "text": (f"🧠 **MLB v6.1 Admin Panel Control Interface**\n"
                     f"━━━━━━━━━━━━━━━━━━\n"
                     f"Current Status Config: `{config_state['SYSTEM_MODE']}`\n"
                     f"Active Session Flag: `{config_state['is_session_active']}`\n"
                     f"━━━━━━━━━━━━━━━━━━\n"
                     f"Choose runtime behavior configuration:"),
            "reply_markup": reply_markup
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[{get_log_time()}] ⚠️ [PANEL SEND ERROR] {e}", flush=True)

def edit_admin_panel(target_chat_id, message_id, new_text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
        payload = {"chat_id": target_chat_id, "message_id": message_id, "text": new_text, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def answer_callback_query(callback_query_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
        requests.post(url, json={"callback_query_id": callback_query_id}, timeout=5)
    except:
        pass

# --- API DATA FETCH ---
def get_market_data():
    t_str = get_log_time()
    try:
        url_ts = int(time.time()*1000)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://draw.ar-lottery01.com/',
            'Origin': 'https://draw.ar-lottery01.com'
        }
        r = requests.get(API_URL, params={'page':1,'pageSize':20,'_':url_ts}, headers=headers, timeout=6)
        if r.status_code == 200:
            return r.json()['data']['list']
        print(f"[{t_str}] ❌ [API HTTP ERROR] Status Code: {r.status_code}", flush=True)
        return []
    except Exception as api_err:
        print(f"[{t_str}] ❌ [API FETCH ERROR] Connection failed: {api_err}", flush=True)
        return []

# --- 100% ORIGINAL MLB V6.1 LOGIC CORE ---
def calculate_mlb_prediction(history, current_loss_streak):
    t_str = get_log_time()
    if len(history) < 5: 
        return None
        
    processed = []
    for item in reversed(history[:20]):
        num = int(item['number'])
        processed.append({
            'num': num,
            'size': 'S' if num < 5 else 'B',
            'color': item.get('color', 'unknown')
        })
        
    len_p = len(processed)
    l1, l2, l3, l4 = processed[len_p-1], processed[len_p-2], processed[len_p-3], processed[len_p-4]
    
    macro_small = sum(1 for h in processed if h['size'] == 'S')
    macro_big = sum(1 for h in processed if h['size'] == 'B')
    macro_trend = 'S' if macro_small > macro_big else 'B'
    
    last_10 = processed[-10:]
    zero_nine_count = sum(1 for h in last_10 if h['num'] in [0, 9])
    is_trampoline_dead = zero_nine_count > 2
    is_violet_disruption = 'violet' in l1['color']

    is_chop = (l1['size'] != l2['size'] and l2['size'] != l3['size'] and l3['size'] != l4['size'])
    is_trampoline = (l1['num'] in [0, 9]) and not is_trampoline_dead
    is_descending = (l1['num'] < l2['num'] and l1['num'] <= 3)
    is_ascending = (l1['num'] > l2['num'] and l1['num'] >= 6)
    is_3_streak = (l1['size'] == l2['size'] and l2['size'] == l3['size'])
    is_trap = (2 <= l1['num'] <= 7 and 2 <= l2['num'] <= 7 and 2 <= l3['num'] <= 7)
    
    prediction = macro_trend
    logic = 'Brain 1: Master Mind Macro'
    alert = '🟢 Safe'
    
    if current_loss_streak >= 4:
        prediction = 'B' if l1['size'] == 'S' else 'S'
        logic = 'Recovery 4: Absolute Reverse (Trend Broke)'
        alert = '🔴 Red Alert'
    elif current_loss_streak == 3:
        prediction = l1['size']
        logic = 'Recovery 3: Streak Surrender (Mirror)'
        alert = '🔴 Red Alert'
    elif current_loss_streak == 2:
        if l1['size'] == l2['size']:
            prediction = 'B' if l1['size'] == 'S' else 'S'
            logic = 'Recovery 2: Streak Trap (Flip)'
        else:
            prediction = l1['size']
            logic = 'Recovery 2: Chop Trap (Flip)'
        alert = '🟡 Caution'
    elif current_loss_streak == 1:
        if l1['size'] == l2['size']:
            prediction = l1['size']
            logic = 'Recovery 1: Streak Catch (Mirror)'
        else:
            prediction = 'B' if l1['size'] == 'S' else 'S'
            logic = 'Recovery 1: Chop Catch (Alternate)'
        alert = '🟡 Caution'
    elif is_chop:
        prediction = 'B' if l1['size'] == 'S' else 'S'
        logic = 'Brain 5: Chop-Chain Override'
        alert = '🟡 Caution'
    elif is_trampoline:
        prediction = 'B' if l1['num'] == 0 else 'S'
        logic = 'Brain 4: Trampoline Bounce'
        alert = '🔴 Red Alert' if (l1['num'] == l2['num'] or is_violet_disruption) else '🟢 Safe'
    elif is_descending:
        prediction = 'S'
        logic = 'Brain 4: Descending Gravity'
        alert = '🔴 Red Alert' if l1['num'] <= 1 else '🟡 Caution'
    elif is_ascending:
        prediction = 'B'
        logic = 'Brain 4: Ascending Gravity'
        alert = '🔴 Red Alert' if l1['num'] >= 8 else '🟡 Caution'
    elif is_3_streak and not is_trap and not is_violet_disruption:
        prediction = 'B' if l1['size'] == 'S' else 'S'
        logic = 'Brain 2: 3-Streak Breaker'
        alert = '🟡 Caution'
    elif is_trap:
        prediction = macro_trend
        logic = 'Brain 6: Trap Scanner (Follow Macro)'
        alert = '🟡 Caution'
    elif is_violet_disruption:
        prediction = macro_trend
        logic = 'Brain 10: Violet Disruption (Follow Macro)'
        alert = '🟡 Caution'
        
    print(f"[{t_str}] 🧠 [ENGINE MATCH] Choice={prediction} | Rule={logic} | Level={current_loss_streak+1}", flush=True)
    return {"prediction": prediction, "alert": alert, "logic": logic}

def run_prediction_cycle():
    t_str = get_log_time()
    history = get_market_data()
    if not history: return None
    latest_result = history[0]
    next_issue = str(int(latest_result['issueNumber']) + 1)
    loss_streak = abs(stats["curr_streak"]) if stats["curr_streak"] < 0 else 0
    
    pred_res = calculate_mlb_prediction(history, loss_streak)
    if not pred_res: return None
    
    display_pred = "SMALL" if pred_res['prediction'] == 'S' else "BIG"
    msg = (f"🚀 **PREDICTION LIVE**\n━━━━━━━━━━━━━━\n"
           f"🧠 Tool: `MLB v6.1 Shield`\n"
           f"💎 Period: `{next_issue[-5:]}`\n"
           f"⚡ Select: **{display_pred}**\n"
           f"📊 Bet Level: **L{loss_streak + 1}**\n"
           f"━━━━━━━━━━━━━━")
    
    send_tg_message(msg)
    print(f"[{t_str}] ✉️ [TELEGRAM SENT] Target Period {next_issue[-5:]} dispatched.", flush=True)
    return {"issue": next_issue, "prediction": pred_res['prediction'], "alert": pred_res['alert']}

def check_round_result(last_pred):
    t_str = get_log_time()
    history = get_market_data()
    if not history: return False
    found = next((x for x in history if x['issueNumber'] == last_pred['issue']), None)
    if not found:
        print(f"[{t_str}] ⏳ [RESULT MATRIX] Period {last_pred['issue']} not ready yet.", flush=True)
        return False
        
    act_num = int(found['number'])
    act_size = 'S' if act_num < 5 else 'B'
    
    print(f"[{t_str}] 📊 [EVALUATION] Period {last_pred['issue']} -> Pred: {last_pred['prediction']} | Act: {act_size}", flush=True)
    
    if last_pred['prediction'] == act_size:
        stats["wins"] += 1
        stats["curr_streak"] = stats["curr_streak"] + 1 if stats["curr_streak"] > 0 else 1
        stats["max_win_streak"] = max(stats["max_win_streak"], stats["curr_streak"])
        send_tg_message("✅ **WINNER!** 🏆💰🔥🎰")
    else:
        stats["losses"] += 1
        stats["curr_streak"] = stats["curr_streak"] - 1 if stats["curr_streak"] < 0 else -1
        stats["max_loss_streak"] = max(stats["max_loss_streak"], abs(stats["curr_streak"]))
        send_tg_message("❌ **LOSS** 📉")
    return True

# --- TELEGRAM Updates Poller ---
def poll_telegram_commands(offset):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        r = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=5)
        if r.status_code == 200:
            updates = r.json().get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                
                if "message" in u and "text" in u["message"]:
                    msg = u["message"]
                    if msg["text"] == "/admin":
                        print(f"[{get_log_time()}] 🛡️ [ADMIN CONTROL] Panel requested by admin.", flush=True)
                        send_admin_panel(msg["chat"]["id"])
                        
                if "callback_query" in u:
                    cb = u["callback_query"]
                    cb_id = cb["id"]
                    cb_data = cb["data"]
                    chat_id = cb["message"]["chat"]["id"]
                    msg_id = cb["message"]["message_id"]
                    
                    answer_callback_query(cb_id)
                    if cb_data == "mode_intime":
                        config_state["SYSTEM_MODE"] = "IN_TIME"
                        print(f"[{get_log_time()}] ⚙️ [MODE SWITCH] Mode changed to IN_TIME", flush=True)
                        edit_admin_panel(chat_id, msg_id, "✅ **Switch Mode Locked Successfully!**\nSystem Rule Applied: `⏰ IN TIME (Target Session Slots Block)`")
                    elif cb_data == "mode_everytime":
                        config_state["SYSTEM_MODE"] = "EVERY_TIME"
                        print(f"[{get_log_time()}] ⚙️ [MODE SWITCH] Mode changed to EVERY_TIME", flush=True)
                        edit_admin_panel(chat_id, msg_id, "✅ **Switch Mode Locked Successfully!**\nSystem Rule Applied: `🔄 EVERY TIME (24/7 Continuous Signals)`")
        elif r.status_code == 409:
            print(f"[{get_log_time()}] ⚠️ [TG API CONFLICT] HTTP 409: Another session is grabbing updates. Retrying cleanup loop...", flush=True)
            time.sleep(2)  # Cooldown rate controller
        else:
            print(f"[{get_log_time()}] ⚠️ [TG POLL CODE] Server returned HTTP {r.status_code}", flush=True)
    except Exception as poll_err:
        print(f"[{get_log_time()}] ⚠️ [TG POLL EXCEPTION] Connection status: {poll_err}", flush=True)
    return offset

# --- ENGINE CORE WATCHDOG ---
def main():
    print(f"[{get_log_time()}] 🚀 [SYSTEM INITIATION] Booting Pydroid 3 Safe Matrix Stack...", flush=True)
    
    # --- AUTOMATIC WEBHOOK FLUSH INJECTION ---
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        print(f"[{get_log_time()}] 🔄 [CLEANUP] Executed session flush on Telegram API server. Active conflicting profile wiped.", flush=True)
    except:
        pass
        
    print(f"[{get_log_time()}] 📡 [WATCHDOG] Active and polling Telegram... Current Mode: IN_TIME.", flush=True)
    tg_offset = 0
    
    while True:
        try:
            now = datetime.now(ist)
            current_minute_str = now.strftime('%Y-%m-%d %H:%M')
            current_slot, next_slot = get_session_schedule()
            
            should_run = (config_state["SYSTEM_MODE"] == "EVERY_TIME") or (config_state["SYSTEM_MODE"] == "IN_TIME" and current_slot is not None)
            
            # Start Session
            if should_run and not config_state["is_session_active"]:
                config_state["is_session_active"] = True
                global stats
                stats = {"wins": 0, "losses": 0, "max_win_streak": 0, "max_loss_streak": 0, "curr_streak": 0}
                config_state["last_prediction_data"] = None
                label = current_slot if current_slot else "24/7 NON-STOP MACHINE"
                print(f"[{get_log_time()}] 🔔 [SESSION START] Online for: {label}", flush=True)
                send_tg_message(f"🔔 **SESSION STARTED ({label})** 🚀🔥\nMLB v6.1 Matrix Online.")
                continue

            # End Session
            if config_state["is_session_active"] and not should_run and config_state["last_prediction_data"] is None and stats["curr_streak"] >= 0:
                config_state["is_session_active"] = False
                print(f"[{get_log_time()}] 🏁 [SESSION END] Telemetry saved.", flush=True)
                summary = (f"🏁 **SESSION COMPLETED REPORT** 🏆👑\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"⚙️ Runtime Environment: `{config_state['SYSTEM_MODE']}`\n"
                           f"✅ Total Wins Recorded: `{stats['wins']}`\n"
                           f"❌ Total Losses Tracked: `{stats['losses']}`\n"
                           f"🏆 Maximum Win Streak: `{stats['max_win_streak']}`\n"
                           f"🔥 Max Loss Level Hit: `L{stats['max_loss_streak'] + 1 if stats['max_loss_streak'] > 0 else 1}`\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"⏰ **Next Target Schedule Block Window:** `{next_slot}`")
                send_tg_message(summary)
                continue

            # Dynamic Clock Trigger Block
            if config_state["is_session_active"] and now.second >= 3 and config_state["last_minute_triggered"] != current_minute_str:
                config_state["last_minute_triggered"] = current_minute_str
                print(f"[{get_log_time()}] ⏰ [CLOCK TRIGGER] Processing 03s+ block...", flush=True)
                
                if config_state["last_prediction_data"]:
                    check_round_result(config_state["last_prediction_data"])
                    config_state["last_prediction_data"] = None 
                
                if should_run or stats["curr_streak"] < 0:
                    time.sleep(0.5) 
                    config_state["last_prediction_data"] = run_prediction_cycle()

            # Instant Telegram Polling
            tg_offset = poll_telegram_commands(tg_offset)
            
        except Exception as e:
            print(f"[{get_log_time()}] ⚠️ [LOOP ERROR] {e}", flush=True)
            
        time.sleep(0.3)

if __name__ == "__main__":
    main()
