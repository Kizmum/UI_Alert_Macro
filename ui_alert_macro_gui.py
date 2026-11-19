from __future__ import annotations

import ctypes
import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

import cv2
import mss
import numpy as np

VERSION = "5.3"
EXPERIMENTAL = False
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "app_config.json"
LEGACY_REGION_PATH = BASE_DIR / "region_config.json"

EVENTS = {
    "rainy_world": ("Rainy World", ("rn1.png", "rn2.png")),
    "blood_moon": ("Blood Moon", ("bm1.png", "bm2.png")),
    "cosmic_nebula": ("Cosmic Nebula", ("cn1.png", "cn2.png")),
    "celestial_moon": ("Celestial Moon", ("cm1.png", "cm2.png")),
    "cryogenic_world": ("Cryogenic World", ("cw1.png", "cw2.png")),
    "mortal_blackout": ("The Mortal Blackout", ("tmb1.png", "tmb2.png", "tmb3.png")),
    "gray_shadow_space": ("The Gray Shadow Space", ("tgss1.png", "tgss2.png", "tgss3.png")),
    "crimson_trigon": ("The Crimson Trigon", ("tct1.png", "tct2.png")),
    "veylune": ("Veylune", ("v1.png", "v2.png")),
}

STANDARD_THRESHOLDS = {key: 0.66 for key in EVENTS}
MIN_SCORE_GAP = 0.05
FAMILY_MISMATCH_PENALTY = 0.55
CHECK_INTERVAL = 5.0
TGSS_FAST_INTERVAL = 0.75
TGSS_LEGACY_INTERVAL = 2.5
TGSS_SUSPECT_DURATION = 8.0
TGSS_SUSPECT_MARGIN = 0.12
TGSS_KEY = "gray_shadow_space"
LEGACY_MATCH_THRESHOLD = 0.76
LEGACY_MIN_SCORE_GAP = 0.025
LEGACY_EVENT_KEYS = (
    "rainy_world", "blood_moon", "cosmic_nebula", "celestial_moon",
    "cryogenic_world", "mortal_blackout", "gray_shadow_space"
)
# Alert cooldowns are per (workspace, biome), not per Discord role.
BIOME_COOLDOWN_SECONDS = {key: (6 * 60 if key in ("rainy_world", "blood_moon") else 12 * 60) for key in EVENTS}
GSS_MULTI_INTERVAL_SECONDS = 5
GSS_MULTI_WINDOW_SECONDS = 2 * 60
GSS_MULTI_MAX_PINGS = 5
COMPARE_SIZE = (220, 140)
VK_F1 = 0x70
VK_F2 = 0x71
MAX_WINDOWS = 8
QUALITY_HEIGHT = {"360p": 360, "480p": 480, "720p": 720, "1080p": 1080, "2K": 1440}
COLOR_CHOICES = ("#e34545", "#488ade", "#2fa568", "#d69927", "#ad6cce", "#16a3a3")
DEFAULT_REGION = {"left": 0, "top": 162, "width": 135, "height": 107}

THEMES = {
    "light": {"bg": "#f3f3f3", "panel": "#f3f3f3", "fg": "#111111", "muted": "#555555",
              "entry": "#ffffff", "button": "#f0f0f0", "active": "#e0e0e0", "border": "#b8b8b8",
              "tab": "#e8e8e8", "tab_active": "#ffffff"},
    "dark": {"bg": "#111214", "panel": "#17191d", "fg": "#f1f1f1", "muted": "#aeb3ba",
             "entry": "#22252a", "button": "#24272c", "active": "#353a42", "border": "#3b3f46",
             "tab": "#1c1f24", "tab_active": "#292d33"},
}

I18N = {
    "en": {
        "main": "Main", "settings": "Settings and Other", "credits": "Credits", "developer": "Developer",
        "start": "START", "stop": "STOP", "stopped": "Stopped", "running": "RUNNING",
        "all_hint": "F1 starts all windows · F2 stops all windows",
        "vip": "VIP server link", "save": "Save", "area_show": "Show area", "area_hide": "Hide area",
        "area_hint": "Drag the selected area or resize its edges.", "overlay_text": "MACRO AREA\ndrag / resize",
        "locked": "Stop this window to edit the detection area.", "last": "Last", "match": "Match",
        "second": "second", "threshold": "threshold", "looks_like": "Looks like", "not_confirmed": "not confirmed",
        "webhook": "Discord webhook URL", "roles": "Discord role IDs for alerts",
        "roles_hint": "ONLY digits are accepted; you can also paste a full role mention (<@&ID>).",
        "language": "Language", "theme": "Theme", "english": "English", "russian": "Russian",
        "light": "Light", "dark": "Dark", "save_apply": "Save & Apply Settings",
        "saved": "Settings saved.", "screenshot_options": "Screenshot options",
        "crop_only": "Screenshot only the selected area", "crop_margin": "Capture slightly beyond the detection area (+25 px, recommended)",
        "reset": "Reset settings", "reset_confirm": "Reset settings except webhook, role IDs and VIP links?",
        "dev_enable": "Developer settings", "dev_warning": "This feature offers additional macro controls. Incorrect settings may cause problems or unwanted behavior.\nUse at your own risk!",
        "dev_thresholds": "Detection thresholds", "dev_quality": "Screenshot quality",
        "gss_multi": "Multi-ping to make SURE you don't miss TGSS (recommended)",
        "standard": "Default", "per_biome": "Per-biome screenshot quality", "global_quality": "Global quality",
        "reset_one": "Reset", "global_choice": "Use global",
        "credits_by": "Created by", "credits_thanks": "Thanks for using UI Alert Macro.",
        "add_window": "New window", "remove_window": "Delete this window?", "choose_color": "Choose detection area color",
        "maximum": "Maximum 8 windows.", "bad_webhook": "Enter a valid Discord webhook URL.",
        "bad_vip": "VIP server link must start with http:// or https://.",
        "missing_discord": "Set the webhook and at least one role ID in Settings.",
        "missing_templates": "UI image templates are missing.", "screenshot": "Screenshot",
        "error": "Error", "info": "Info",
        "biome_on": "Enable detection", "window_on": "Window enabled", "disabled": "Disabled",
    },
    "ru": {
        "main": "Главная", "settings": "Настройки и другое", "credits": "Создатели", "developer": "Для разработчиков",
        "start": "START", "stop": "STOP", "stopped": "Остановлено", "running": "РАБОТАЕТ",
        "all_hint": "F1 запускает все окна · F2 останавливает все окна",
        "vip": "Ссылка на VIP server", "save": "Сохранить", "area_show": "Показать область", "area_hide": "Спрятать область",
        "area_hint": "Перетаскивай выделенную область или растягивай за края.", "overlay_text": "ОБЛАСТЬ МАКРОСА\nперетащи / растяни",
        "locked": "Останови это окно, чтобы изменить область.", "last": "Последнее", "match": "Совпадение",
        "second": "второе", "threshold": "порог", "looks_like": "Похоже на", "not_confirmed": "не подтверждено",
        "webhook": "Discord webhook URL", "roles": "ID ролей для пингов",
        "roles_hint": "Допускаются ТОЛЬКО цифры. Можно вставить упоминание роли целиком (<@&ID>).",
        "language": "Язык", "theme": "Тема", "english": "English", "russian": "Русский",
        "light": "Светлая", "dark": "Тёмная", "save_apply": "Сохранить и применить",
        "saved": "Настройки сохранены.", "screenshot_options": "Настройки скриншотов",
        "crop_only": "Скриншот только выделенной зоны", "crop_margin": "Скриншот чуть больше области определения (+25 px, рекомендуется)",
        "reset": "Сбросить настройки", "reset_confirm": "Сбросить настройки, кроме webhook, ID ролей и VIP-ссылок?",
        "dev_enable": "Для разработчиков", "dev_warning": "Эта функция была добавлена для дополнительных возможностей макроса, но при неправильном использовании или настройке может повредить макрос или доставить иных хлопот.\nИспользуйте только на свой страх и риск!",
        "dev_thresholds": "Пороги обнаружения", "dev_quality": "Качество скриншотов",
        "gss_multi": "Мульти пинг, чтобы ТОЧНО не пропустить TGSS (рекомендуется)",
        "standard": "Стандарт", "per_biome": "Качество для каждого биома", "global_quality": "Глобальное качество",
        "reset_one": "Сброс", "global_choice": "Глобальное",
        "credits_by": "Создатели", "credits_thanks": "Спасибо за использование UI Alert Macro.",
        "add_window": "Новое окно", "remove_window": "Удалить это окно?", "choose_color": "Выбрать цвет области",
        "maximum": "Максимум 8 окон.", "bad_webhook": "Введи правильный Discord webhook URL.",
        "bad_vip": "Ссылка на VIP server должна начинаться с http:// или https://.",
        "missing_discord": "Укажи webhook и хотя бы один Role ID в настройках.",
        "missing_templates": "Не найдены изображения UI.", "screenshot": "Скриншот",
        "error": "Ошибка", "info": "Информация",
        "biome_on": "Включить обнаружение", "window_on": "Вкладка включена", "disabled": "Отключено",
    },
}


def default_window(index: int = 1) -> dict:
    return {"id": "main" if index == 1 else uuid.uuid4().hex[:12], "name": f"Window {index}",
            "region": deepcopy(DEFAULT_REGION), "color": COLOR_CHOICES[(index - 1) % len(COLOR_CHOICES)],
            "vip_url": "", "running": False, "enabled": True, "overlay_shown": True}


def default_config() -> dict:
    return {"config_version": "5.3", "webhook_url": "", "role_ids": {k: "" for k in EVENTS}, "biome_enabled": {k: False for k in EVENTS}, "language": "en", "theme": "light",
            "crop_only": False, "crop_margin": True, "developer": False, "gss_multi_ping": True, "thresholds": dict(STANDARD_THRESHOLDS),
            "global_quality": "1080p", "biome_quality": {k: "global" for k in EVENTS},
            "windows": [default_window()]}


def digits(text: str) -> str:
    return re.sub(r"[^0-9]", "", str(text))


def normalize_region(value: object) -> dict:
    if not isinstance(value, dict):
        return deepcopy(DEFAULT_REGION)
    try:
        return {"left": int(value["left"]), "top": int(value["top"]),
                "width": max(50, int(value["width"])), "height": max(40, int(value["height"]))}
    except (KeyError, ValueError, TypeError):
        return deepcopy(DEFAULT_REGION)


def load_config() -> dict:
    cfg = default_config()
    if not CONFIG_PATH.exists():
        if LEGACY_REGION_PATH.exists():
            try:
                cfg["windows"][0]["region"] = normalize_region(json.loads(LEGACY_REGION_PATH.read_text(encoding="utf-8")))
            except (ValueError, OSError):
                pass
        return cfg
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    if not isinstance(data, dict):
        return cfg
    cfg["webhook_url"] = str(data.get("webhook_url", ""))
    for key in EVENTS:
        cfg["role_ids"][key] = digits(data.get("role_ids", {}).get(key, "")) if isinstance(data.get("role_ids"), dict) else ""
    # A v5.0 configuration has no switches: populated roles start enabled.
    enabled_saved = data.get("biome_enabled")
    for key in EVENTS:
        role_id = cfg["role_ids"][key]
        if isinstance(enabled_saved, dict) and isinstance(enabled_saved.get(key), bool):
            cfg["biome_enabled"][key] = bool(enabled_saved[key]) and bool(role_id)
        else:
            cfg["biome_enabled"][key] = bool(role_id)
    for key, options in (("language", I18N), ("theme", THEMES), ("global_quality", QUALITY_HEIGHT)):
        if data.get(key) in options:
            cfg[key] = data[key]
    for key in ("crop_only", "crop_margin", "developer", "gss_multi_ping"):
        if isinstance(data.get(key), bool):
            cfg[key] = data[key]
    for key in EVENTS:
        try:
            v = float(data.get("thresholds", {}).get(key, STANDARD_THRESHOLDS[key]))
            if 0.01 <= v <= 1.0:
                # 5.1 used 0.63 for TGSS. Update only the old default value
                # when importing settings, retaining explicit custom values.
                if key == "gray_shadow_space" and str(data.get("config_version", "")) not in ("5.2", "5.3") and abs(v - 0.63) < 1e-9:
                    v = STANDARD_THRESHOLDS[key]
                cfg["thresholds"][key] = v
        except (ValueError, TypeError, AttributeError):
            pass
        bq = data.get("biome_quality", {})
        if isinstance(bq, dict) and bq.get(key) in ("global", *QUALITY_HEIGHT):
            cfg["biome_quality"][key] = bq[key]
    windows = data.get("windows")
    if isinstance(windows, list) and windows:
        valid = []
        seen = set()
        for idx, w in enumerate(windows[:MAX_WINDOWS], 1):
            if not isinstance(w, dict):
                continue
            item = default_window(idx)
            item["id"] = str(w.get("id") or item["id"])
            if item["id"] in seen:
                item["id"] = uuid.uuid4().hex[:12]
            seen.add(item["id"])
            item["name"] = str(w.get("name") or item["name"])[:24]
            item["region"] = normalize_region(w.get("region"))
            col = str(w.get("color", item["color"]))
            if re.fullmatch(r"#[0-9a-fA-F]{6}", col):
                item["color"] = col
            item["vip_url"] = str(w.get("vip_url", ""))
            item["overlay_shown"] = bool(w.get("overlay_shown", True))
            item["enabled"] = bool(w.get("enabled", True))
            valid.append(item)
        if valid:
            cfg["windows"] = valid
    else:
        # Migration from 4.x configuration.
        cfg["windows"][0]["vip_url"] = str(data.get("vip_server_url", ""))
        if LEGACY_REGION_PATH.exists():
            try:
                cfg["windows"][0]["region"] = normalize_region(json.loads(LEGACY_REGION_PATH.read_text(encoding="utf-8")))
            except (ValueError, OSError):
                pass
    return cfg


def save_config(cfg: dict) -> None:
    data = deepcopy(cfg)
    for w in data["windows"]:
        w["running"] = False
    temp = CONFIG_PATH.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(CONFIG_PATH)


def enable_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def key_pressed(code: int) -> bool:
    return bool(os.name == "nt" and ctypes.windll.user32.GetAsyncKeyState(code) & 1)

def trim_dark_outer_border(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = (gray > 10).astype(np.uint8) * 255
    points = cv2.findNonZero(mask)

    if points is None:
        return image

    x, y, w, h = cv2.boundingRect(points)
    if w * h < image.shape[0] * image.shape[1] * 0.15:
        return image

    pad = 2
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(image.shape[1], x + w + pad)
    y2 = min(image.shape[0], y + h + pad)
    return image[y1:y2, x1:x2]


def normalize_image(image: np.ndarray) -> np.ndarray:
    image = trim_dark_outer_border(image)
    image = cv2.resize(image, COMPARE_SIZE, interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(image, (3, 3), 0)


def correlation_01(a: np.ndarray, b: np.ndarray) -> float:
    value = float(cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED)[0, 0])
    if not np.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, (value + 1.0) / 2.0))


def structural_similarity(a: np.ndarray, b: np.ndarray) -> float:
    gray_a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    gray_score = correlation_01(gray_a, gray_b)

    edge_a = cv2.Canny(gray_a, 45, 140)
    edge_b = cv2.Canny(gray_b, 45, 140)
    edge_score = correlation_01(edge_a, edge_b)

    lab_a = cv2.cvtColor(a, cv2.COLOR_BGR2LAB)
    lab_b = cv2.cvtColor(b, cv2.COLOR_BGR2LAB)
    chroma_score = (
        correlation_01(lab_a[:, :, 1], lab_b[:, :, 1])
        + correlation_01(lab_a[:, :, 2], lab_b[:, :, 2])
    ) / 2.0

    return 0.58 * gray_score + 0.22 * edge_score + 0.20 * chroma_score


def _normalized_hist(values: np.ndarray, bins: int, max_value: int, mask: np.ndarray | None = None) -> np.ndarray:
    if mask is None:
        hist = cv2.calcHist([values], [0], None, [bins], [0, max_value]).flatten().astype(np.float32)
    else:
        hist = cv2.calcHist([values], [0], mask.astype(np.uint8), [bins], [0, max_value]).flatten().astype(np.float32)
    total = float(hist.sum())
    if total > 0:
        hist /= total
    return hist


def build_color_profile(image: np.ndarray) -> dict[str, object]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    visible = v > 18
    colorful = visible & (s > 20)

    hue_bins = 24
    bin_index = np.minimum((h.astype(np.int32) * hue_bins // 180), hue_bins - 1)
    weights = (s.astype(np.float32) / 255.0) * (v.astype(np.float32) / 255.0)
    hue_hist = np.zeros(hue_bins, dtype=np.float32)
    for i in range(hue_bins):
        hue_hist[i] = float(weights[(bin_index == i) & colorful].sum())
    hue_total = float(hue_hist.sum())
    if hue_total > 0:
        hue_hist /= hue_total

    sat_hist = _normalized_hist(s, 8, 256, visible)
    val_hist = _normalized_hist(v, 8, 256, None)

    hv = h[visible]
    sv = s[visible]

    if hv.size == 0:
        return {
            "hue_hist": hue_hist,
            "sat_hist": sat_hist,
            "val_hist": val_hist,
            "family": "unknown",
        }

    red_fraction = float(((((hv < 15) | (hv > 165)) & (sv > 55))).mean())
    blue_fraction = float((((hv >= 80) & (hv <= 135) & (sv > 45))).mean())
    gray_fraction = float((sv < 55).mean())
    mean_saturation = float(sv.mean())

    if red_fraction >= 0.22 and red_fraction > blue_fraction * 1.25:
        family = "red"
    elif mean_saturation < 78 or gray_fraction > 0.52:
        family = "gray"
    elif blue_fraction >= 0.22:
        family = "blue"
    else:
        family = "unknown"

    return {
        "hue_hist": hue_hist,
        "sat_hist": sat_hist,
        "val_hist": val_hist,
        "family": family,
    }


def histogram_similarity(a: np.ndarray, b: np.ndarray) -> float:
    distance = float(cv2.compareHist(a.astype(np.float32), b.astype(np.float32), cv2.HISTCMP_BHATTACHARYYA))
    if not np.isfinite(distance):
        return 0.0
    return max(0.0, min(1.0, 1.0 - distance))


def color_profile_similarity(a: dict[str, object], b: dict[str, object]) -> float:
    hue_score = histogram_similarity(a["hue_hist"], b["hue_hist"])
    sat_score = histogram_similarity(a["sat_hist"], b["sat_hist"])
    val_score = histogram_similarity(a["val_hist"], b["val_hist"])
    return 0.60 * hue_score + 0.25 * sat_score + 0.15 * val_score



@dataclass
class DetectionResult:
    event_key: str | None
    best_key: str
    score: float
    second_score: float
    threshold: float


@dataclass
class LegacyTGSSResult:
    detected: bool
    best_key: str
    tgss_score: float
    second_score: float
    threshold: float = LEGACY_MATCH_THRESHOLD


def legacy_image_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Original v2 matching weights, unchanged: gray / edges / RGB histogram."""
    gray_a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    gray_score = correlation_01(gray_a, gray_b)
    edge_score = correlation_01(cv2.Canny(gray_a, 50, 150), cv2.Canny(gray_b, 50, 150))
    hist_a = cv2.calcHist([a], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist_b = cv2.calcHist([b], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist_a, hist_a)
    cv2.normalize(hist_b, hist_b)
    raw = float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))
    hist_score = max(0.0, min(1.0, (raw + 1.0) / 2.0)) if np.isfinite(raw) else 0.0
    return 0.55 * gray_score + 0.25 * edge_score + 0.20 * hist_score


def load_legacy_templates() -> dict[str, np.ndarray]:
    """Seven original v2 references; used only to decide whether TGSS is present."""
    result = {}
    for key in LEGACY_EVENT_KEYS:
        path = BASE_DIR / "legacy_ui" / (key + ".png")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Missing legacy UI image: {path}")
        result[key] = normalize_image(image)
    return result


def detect_tgss_legacy(image: np.ndarray, templates: dict[str, np.ndarray]) -> LegacyTGSSResult:
    """Original v2 0.76 threshold and 0.025 runner-up gap. Other biomes cannot ping."""
    scores = sorted(((legacy_image_similarity(image, template), key)
                     for key, template in templates.items()), reverse=True)
    if not scores:
        return LegacyTGSSResult(False, "", 0.0, 0.0)
    best_score, best_key = scores[0]
    tgss_score = next((score for score, key in scores if key == TGSS_KEY), 0.0)
    second = scores[1][0] if len(scores) > 1 else 0.0
    detected = (best_key == TGSS_KEY and best_score >= LEGACY_MATCH_THRESHOLD
                and best_score - second >= LEGACY_MIN_SCORE_GAP)
    return LegacyTGSSResult(detected, best_key, tgss_score, second)


def modern_tgss_score(screen_image: np.ndarray, variants: list[dict]) -> float:
    """Same v5.2 TGSS scoring formula, but evaluates ONLY its three templates."""
    if not variants:
        return 0.0
    screen_color = build_color_profile(screen_image)
    family = str(screen_color["family"])
    best = 0.0
    for variant in variants:
        structure = structural_similarity(screen_image, variant["image"])
        color = color_profile_similarity(screen_color, variant["color"])
        score = 0.54 * structure + 0.46 * color
        variant_family = str(variant["color"]["family"])
        if family != "unknown" and variant_family != "unknown" and family != variant_family:
            score *= FAMILY_MISMATCH_PENALTY
        best = max(best, score)
    return best


def tgss_is_suspected(score: float, threshold: float) -> bool:
    return score >= max(0.0, threshold - TGSS_SUSPECT_MARGIN)


def load_templates() -> dict[str, list[dict]]:
    templates = {}
    for key, (_, files) in EVENTS.items():
        variants = []
        for filename in files:
            path = BASE_DIR / "ui" / filename
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                raise FileNotFoundError(f"Image not found: ui/{filename}")
            img = normalize_image(image)
            variants.append({"image": img, "color": build_color_profile(img)})
        templates[key] = variants
    return templates


def capture_region(sct: mss.mss, region: dict) -> np.ndarray:
    grab = np.array(sct.grab(region), dtype=np.uint8)
    return normalize_image(cv2.cvtColor(grab, cv2.COLOR_BGRA2BGR))


def detect_event(screen_image: np.ndarray, templates: dict[str, list[dict]], thresholds: dict,
                 enabled_keys: set[str] | None = None) -> DetectionResult:
    if enabled_keys is not None and not enabled_keys:
        return DetectionResult(None, "", 0.0, 0.0, 0.0)
    screen_color = build_color_profile(screen_image)
    family = str(screen_color["family"])
    biome_scores = []
    for key, variants in templates.items():
        best = 0.0
        for variant in variants:
            structure = structural_similarity(screen_image, variant["image"])
            color = color_profile_similarity(screen_color, variant["color"])
            score = 0.54 * structure + 0.46 * color
            variant_family = str(variant["color"]["family"])
            if family != "unknown" and variant_family != "unknown" and family != variant_family:
                score *= FAMILY_MISMATCH_PENALTY
            best = max(best, score)
        biome_scores.append((best, key))
    biome_scores.sort(reverse=True)
    if not biome_scores:
        return DetectionResult(None, "", 0.0, 0.0, 0.0)
    eligible = [item for item in biome_scores if enabled_keys is None or item[1] in enabled_keys]
    if not eligible:
        return DetectionResult(None, "", 0.0, 0.0, 0.0)
    score, key = eligible[0]
    # Disabled biomes remain competitors for ambiguity checks, but can never trigger alerts.
    second = max((v for v, other_key in biome_scores if other_key != key), default=0.0)
    threshold = float(thresholds.get(key, STANDARD_THRESHOLDS[key]))
    detected = key if score >= threshold and score - second >= MIN_SCORE_GAP else None
    return DetectionResult(detected, key, score, second, threshold)


def is_valid_webhook(url: str) -> bool:
    return url.startswith("https://discord.com/api/webhooks/") or url.startswith("https://discordapp.com/api/webhooks/")


def monitor_for_region(sct: mss.mss, region: dict) -> dict:
    cx, cy = region["left"] + region["width"] // 2, region["top"] + region["height"] // 2
    for monitor in sct.monitors[1:]:
        if monitor["left"] <= cx < monitor["left"] + monitor["width"] and monitor["top"] <= cy < monitor["top"] + monitor["height"]:
            return monitor
    return sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]


def screenshot_jpeg(sct: mss.mss, region: dict, cfg: dict, key: str) -> tuple[bytes, str]:
    monitor = monitor_for_region(sct, region)
    if cfg["crop_only"]:
        margin = 25 if cfg["crop_margin"] else 0
        left = max(monitor["left"], region["left"] - margin)
        top = max(monitor["top"], region["top"] - margin)
        right = min(monitor["left"] + monitor["width"], region["left"] + region["width"] + margin)
        bottom = min(monitor["top"] + monitor["height"], region["top"] + region["height"] + margin)
        bounds = {"left": left, "top": top, "width": max(1, right - left), "height": max(1, bottom - top)}
    else:
        bounds = monitor
    shot = np.array(sct.grab(bounds), dtype=np.uint8)
    bgr = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
    selection = cfg["biome_quality"].get(key, "global")
    quality = cfg["global_quality"] if selection == "global" else selection
    max_height = QUALITY_HEIGHT.get(quality, 1080)
    h, w = bgr.shape[:2]
    if h > max_height:
        new_w = max(1, round(w * max_height / h))
        bgr = cv2.resize(bgr, (new_w, max_height), interpolation=cv2.INTER_AREA)
    success, encoded = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not success:
        raise RuntimeError("Screenshot encoding failed")
    return encoded.tobytes(), time.strftime("ui_alert_%Y%m%d_%H%M%S.jpg")


def discord_payload(role_id: str, event_key: str, vip_url: str, filename: str,
                    tgss_diagnostics: dict | None = None) -> dict:
    # Discord notification text is always English.
    content = f"<@&{role_id}> **{EVENTS[event_key][0]}** detected!"
    if vip_url:
        content += f"\n🔗 VIP server: {vip_url}"
    if tgss_diagnostics and event_key == TGSS_KEY:
        d = tgss_diagnostics
        modern = d["modern"]
        legacy = d["legacy"]
        content += (
            "\n\n**TGSS diagnostics (v5.3 EX)**"
            f"\nTriggered by: **{d['trigger']}**"
            f"\nModern TGSS: {d['modern_tgss_score']:.3f} / {d['modern_threshold']:.3f}"
            f" | best: {modern.best_key} ({modern.score:.3f})"
            f" | second: {modern.second_score:.3f}"
            f" | pass: {'YES' if modern.event_key == TGSS_KEY else 'NO'}"
            f"\nLegacy TGSS: {legacy.tgss_score:.3f} / {legacy.threshold:.3f}"
            f" | best: {legacy.best_key} | second: {legacy.second_score:.3f}"
            f" | pass: {'YES' if legacy.detected else 'NO'}"
        )
    return {
        "content": content,
        "allowed_mentions": {"parse": [], "roles": [role_id]},
        "attachments": [{"id": 0, "filename": filename,
                         "description": f"Screenshot of {EVENTS[event_key][0]} detection"}],
    }


def build_multipart(payload: dict, screenshot: bytes, filename: str) -> tuple[bytes, str]:
    boundary = "----UIAlertMacro" + uuid.uuid4().hex
    parts = [f"--{boundary}\r\n".encode(), b'Content-Disposition: form-data; name="payload_json"\r\n',
             b'Content-Type: application/json\r\n\r\n', json.dumps(payload, ensure_ascii=False).encode(), b'\r\n',
             f'--{boundary}\r\n'.encode(),
             f'Content-Disposition: form-data; name="files[0]"; filename="{filename}"\r\n'.encode(),
             b'Content-Type: image/jpeg\r\n\r\n', screenshot, b'\r\n', f'--{boundary}--\r\n'.encode()]
    return b''.join(parts), boundary


def send_discord_ping(key: str, role_id: str, webhook: str, vip_url: str, image: bytes, filename: str,
                      tgss_diagnostics: dict | None = None) -> tuple[bool, str]:
    payload = discord_payload(role_id, key, vip_url, filename, tgss_diagnostics)
    data, boundary = build_multipart(payload, image, filename)
    request = urllib.request.Request(webhook, data=data, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "UI-Alert-Macro/5.3"})
    try:
        with urllib.request.urlopen(request, timeout=18) as response:
            code = response.status
        return 200 <= code < 300, f"Discord: sent, HTTP {code}"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:220]
        return False, f"Discord HTTP {exc.code}: {detail}"
    except (urllib.error.URLError, OSError) as exc:
        return False, f"Discord: {exc}"

class CooldownTracker:
    """Successful-send cooldowns scoped to one workspace and one biome."""

    def __init__(self):
        self.cooldown_until: dict[tuple[str, str], float] = {}
        self.gss_history: dict[str, list[float]] = {}

    def remaining(self, window_id: str, event_key: str, now: float) -> float:
        return max(0.0, self.cooldown_until.get((window_id, event_key), 0.0) - now)

    def record_success(self, window_id: str, event_key: str, now: float, gss_multi: bool) -> None:
        key = (window_id, event_key)
        if event_key == "gray_shadow_space" and gss_multi:
            history = self.gss_history.setdefault(window_id, [])
            # A burst starts with its first successful notification.
            # If two minutes have elapsed, the next ping starts a new burst.
            if history and now - history[0] > GSS_MULTI_WINDOW_SECONDS:
                history.clear()
            history.append(now)
            if len(history) >= GSS_MULTI_MAX_PINGS:
                self.cooldown_until[key] = now + BIOME_COOLDOWN_SECONDS[event_key]
                history.clear()
            else:
                self.cooldown_until[key] = now + GSS_MULTI_INTERVAL_SECONDS
        else:
            self.cooldown_until[key] = now + BIOME_COOLDOWN_SECONDS[event_key]
            if event_key == "gray_shadow_space":
                self.gss_history.pop(window_id, None)

    def remove_window(self, window_id: str) -> None:
        for key in list(self.cooldown_until):
            if key[0] == window_id:
                self.cooldown_until.pop(key, None)
        self.gss_history.pop(window_id, None)


class RegionOverlay:
    EDGE = 12
    MIN_W = 50
    MIN_H = 40

    def __init__(self, master: tk.Tk, region: dict[str, int], on_change, text: str, color: str = "#ff2020"):
        self.master = master
        self.on_change = on_change
        self.region = region.copy()
        self.color = color

        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.24)
        self.win.configure(bg=self.color)

        self.label = tk.Label(
            self.win,
            text=text,
            bg=self.color,
            fg="white",
            font=("Segoe UI", 9, "bold"),
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        self._action = None
        self._start_pointer = (0, 0)
        self._start_geom = (0, 0, 0, 0)

        for widget in (self.win, self.label):
            widget.bind("<Button-1>", self._mouse_down)
            widget.bind("<B1-Motion>", self._mouse_drag)
            widget.bind("<ButtonRelease-1>", self._mouse_up)
            widget.bind("<Motion>", self._mouse_move)

        self.set_region(region)

    def set_color(self, color: str) -> None:
        self.color = color
        self.win.configure(bg=color)
        self.label.configure(bg=color)

    def set_text(self, text: str) -> None:
        self.label.configure(text=text)

    def _screen_size(self):
        return self.master.winfo_screenwidth(), self.master.winfo_screenheight()

    def set_region(self, region: dict[str, int]):
        self.region = region.copy()
        self.win.geometry(
            f"{self.region['width']}x{self.region['height']}+{self.region['left']}+{self.region['top']}"
        )

    def get_region(self) -> dict[str, int]:
        self.win.update_idletasks()
        return {
            "left": int(self.win.winfo_x()),
            "top": int(self.win.winfo_y()),
            "width": int(self.win.winfo_width()),
            "height": int(self.win.winfo_height()),
        }

    def show(self):
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        self.win.withdraw()

    def visible(self) -> bool:
        return self.win.state() != "withdrawn"

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass

    def _pointer_local(self, event):
        x = event.x_root - self.win.winfo_rootx()
        y = event.y_root - self.win.winfo_rooty()
        return x, y

    def _hit_test(self, event):
        x, y = self._pointer_local(event)
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        e = self.EDGE

        left = x <= e
        right = x >= w - e
        top = y <= e
        bottom = y >= h - e

        if left and top:
            return "nw"
        if right and top:
            return "ne"
        if left and bottom:
            return "sw"
        if right and bottom:
            return "se"
        if left:
            return "w"
        if right:
            return "e"
        if top:
            return "n"
        if bottom:
            return "s"
        return "move"

    def _set_cursor(self, action: str):
        cursors = {
            "nw": "size_nw_se",
            "se": "size_nw_se",
            "ne": "size_ne_sw",
            "sw": "size_ne_sw",
            "n": "size_ns",
            "s": "size_ns",
            "w": "size_we",
            "e": "size_we",
            "move": "fleur",
        }
        cursor = cursors.get(action, "arrow")
        try:
            self.win.configure(cursor=cursor)
            self.label.configure(cursor=cursor)
        except tk.TclError:
            try:
                self.win.configure(cursor="arrow")
            except Exception:
                pass

    def _mouse_move(self, event):
        if self._action is None:
            self._set_cursor(self._hit_test(event))

    def _mouse_down(self, event):
        self._action = self._hit_test(event)
        self._start_pointer = (event.x_root, event.y_root)
        self._start_geom = (
            self.win.winfo_x(),
            self.win.winfo_y(),
            self.win.winfo_width(),
            self.win.winfo_height(),
        )

    def _mouse_drag(self, event):
        if self._action is None:
            return

        sx, sy = self._start_pointer
        x0, y0, w0, h0 = self._start_geom
        dx = event.x_root - sx
        dy = event.y_root - sy

        x, y, w, h = x0, y0, w0, h0
        action = self._action

        if action == "move":
            x = x0 + dx
            y = y0 + dy
        else:
            if "e" in action:
                w = w0 + dx
            if "s" in action:
                h = h0 + dy
            if "w" in action:
                x = x0 + dx
                w = w0 - dx
            if "n" in action:
                y = y0 + dy
                h = h0 - dy

        if w < self.MIN_W:
            if "w" in action:
                x -= self.MIN_W - w
            w = self.MIN_W

        if h < self.MIN_H:
            if "n" in action:
                y -= self.MIN_H - h
            h = self.MIN_H

        screen_w, screen_h = self._screen_size()

        if x < 0:
            if action == "move":
                x = 0
            else:
                w += x
                x = 0
        if y < 0:
            if action == "move":
                y = 0
            else:
                h += y
                y = 0

        if x + w > screen_w:
            if action == "move":
                x = screen_w - w
            else:
                w = screen_w - x
        if y + h > screen_h:
            if action == "move":
                y = screen_h - h
            else:
                h = screen_h - y

        w = max(self.MIN_W, int(w))
        h = max(self.MIN_H, int(h))
        x = int(x)
        y = int(y)

        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.region = {"left": x, "top": y, "width": w, "height": h}
        self.on_change(self.region, save=False)

    def _mouse_up(self, event):
        if self._action is None:
            return
        self._action = None
        self.region = self.get_region()
        self.on_change(self.region, save=True)



class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"UI Alert Macro v{VERSION}")
        self.root.geometry("795x670")
        self.root.minsize(740, 610)
        self.style = ttk.Style(root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.lock = threading.RLock()
        self.config = load_config()
        self.windows = self.config["windows"]
        self.active_id = self.windows[0]["id"]
        self.shutdown = threading.Event()
        self.messages: queue.Queue = queue.Queue()
        self.cooldowns = CooldownTracker()
        self.next_checks: dict[str, float] = {}
        self.next_tgss_legacy: dict[str, float] = {}
        self.next_tgss_fast: dict[str, float] = {}
        self.tgss_suspect_until: dict[str, float] = {}
        self.overlay_map: dict[str, RegionOverlay] = {}
        self.view_results: dict[str, tuple[str, str]] = {}

        try:
            self.templates = load_templates()
            self.legacy_templates = load_legacy_templates()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.templates = {}
            self.legacy_templates = {}

        self._auto_ready = False
        self._autosave_job = None
        self.language_var = tk.StringVar(value=self.config["language"])
        self.theme_var = tk.StringVar(value=self.config["theme"])
        self.webhook_var = tk.StringVar(value=self.config["webhook_url"])
        self.role_vars: dict[str, tk.StringVar] = {
            key: tk.StringVar(value=digits(self.config["role_ids"].get(key, ""))) for key in EVENTS
        }
        self.enabled_vars = {
            key: tk.BooleanVar(value=self.config["biome_enabled"].get(key, False)) for key in EVENTS
        }
        self._last_role_values = {key: self.role_vars[key].get() for key in EVENTS}
        self.window_enabled_var = tk.BooleanVar(value=self.windows[0].get("enabled", True))
        self.vip_var = tk.StringVar(value=self.windows[0]["vip_url"])
        self.crop_var = tk.BooleanVar(value=self.config["crop_only"])
        self.margin_var = tk.BooleanVar(value=self.config["crop_margin"])
        self.dev_var = tk.BooleanVar(value=self.config["developer"])
        self.gss_multi_var = tk.BooleanVar(value=self.config["gss_multi_ping"])
        self.quality_var = tk.StringVar(value=self.config["global_quality"])
        self.threshold_vars = {key: tk.StringVar(value=f"{self.config['thresholds'][key]:.2f}") for key in EVENTS}
        self.biome_quality_vars = {key: tk.StringVar(value=self.config["biome_quality"].get(key, "global")) for key in EVENTS}
        self.status_var = tk.StringVar()
        self.region_var = tk.StringVar()
        self.detect_var = tk.StringVar()
        self.score_var = tk.StringVar()

        self._build_ui()
        for window in self.windows:
            self._create_overlay(window)
        self._refresh_tabstrip()
        self._sync_active_display()
        self._apply_language()
        self._update_developer_tab()
        self._apply_theme_for_tab()
        self._refresh_overlay_visibility()
        self._register_auto_save()

        self.worker = threading.Thread(target=self._monitor_loop, daemon=True)
        self.worker.start()
        root.after(45, self._check_hotkeys)
        root.after(100, self._drain_queue)
        root.protocol("WM_DELETE_WINDOW", self._close)

    def t(self, key: str) -> str:
        return I18N.get(self.language_var.get(), I18N["en"]).get(key, key)

    def _clean_role_var(self, var: tk.StringVar):
        original = var.get()
        cleaned = digits(original)
        if original != cleaned:
            var.set(cleaned)

    def _role_changed(self, key: str):
        var = self.role_vars[key]
        clean = digits(var.get())
        if clean != var.get():
            var.set(clean)
        previous = self._last_role_values.get(key, "")
        self._last_role_values[key] = clean
        if clean != previous:
            self.enabled_vars[key].set(bool(clean))
        self._schedule_autosave()

    def _register_auto_save(self):
        self._auto_ready = True
        for key, var in self.role_vars.items():
            var.trace_add("write", lambda *_a, k=key: self._role_changed(k))
        settings_vars = [self.webhook_var, self.crop_var, self.margin_var,
                         self.language_var, self.theme_var, self.dev_var,
                         self.quality_var, self.gss_multi_var, *self.enabled_vars.values(),
                         *self.threshold_vars.values(), *self.biome_quality_vars.values()]
        for var in settings_vars:
            var.trace_add("write", lambda *_a: self._schedule_autosave())
        self.vip_var.trace_add("write", lambda *_a: self._auto_vip_changed())

    def _auto_vip_changed(self):
        if not self._auto_ready:
            return
        with self.lock:
            window = self._get_window()
            if window is not None:
                window["vip_url"] = self.vip_var.get()
        self._schedule_autosave()

    def _schedule_autosave(self):
        if not self._auto_ready or self.shutdown.is_set():
            return
        # Apply alert routing immediately; debounce only the disk write.
        with self.lock:
            self.config["webhook_url"] = self.webhook_var.get().strip()
            self.config["role_ids"] = {key: digits(var.get()) for key, var in self.role_vars.items()}
            self.config["biome_enabled"] = {
                key: bool(self.enabled_vars[key].get()) and bool(self.config["role_ids"][key])
                for key in EVENTS
            }
            self.config["gss_multi_ping"] = bool(self.gss_multi_var.get())
        if self._autosave_job is not None:
            self.root.after_cancel(self._autosave_job)
        self._autosave_job = self.root.after(300, self._flush_autosave)

    def _flush_autosave(self):
        self._autosave_job = None
        if self.shutdown.is_set():
            return
        try:
            self._save_settings(silent=True)
        except (OSError, tk.TclError) as exc:
            print(f"Settings save failed: {exc}")

    def _get_window(self, window_id: str | None = None) -> dict | None:
        target = window_id or self.active_id
        return next((w for w in self.windows if w["id"] == target), None)

    def _snapshot(self) -> dict:
        with self.lock:
            return deepcopy(self.config)

    def _save(self):
        with self.lock:
            self.config["windows"] = deepcopy(self.windows)
            data = deepcopy(self.config)
        save_config(data)

    def _paste_entry(self, entry: tk.Entry):
        try:
            value = self.root.clipboard_get()
        except tk.TclError:
            return "break"
        try:
            if entry.selection_present():
                entry.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        if entry in self.role_entries.values():
            value = digits(value)
        entry.insert(tk.INSERT, value)
        return "break"

    def _entry_menu(self, event):
        entry = event.widget
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label="Cut" if self.language_var.get() == "en" else "Вырезать", command=lambda: entry.event_generate("<<Cut>>"))
        menu.add_command(label="Copy" if self.language_var.get() == "en" else "Копировать", command=lambda: entry.event_generate("<<Copy>>"))
        menu.add_command(label="Paste" if self.language_var.get() == "en" else "Вставить", command=lambda: self._paste_entry(entry))
        menu.add_separator()
        menu.add_command(label="Select all" if self.language_var.get() == "en" else "Выделить всё",
                         command=lambda: (entry.selection_range(0, tk.END), entry.icursor(tk.END)))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _enable_paste(self, entry: tk.Entry):
        def handle_ctrl(e):
            code = int(getattr(e, "keycode", 0) or 0)
            if str(e.keysym).lower() == "v" or code == 86:
                return self._paste_entry(e.widget)
            return None
        entry.bind("<Control-KeyPress>", handle_ctrl)
        entry.bind("<Shift-Insert>", lambda _e, wid=entry: self._paste_entry(wid))
        entry.bind("<Button-3>", self._entry_menu)

    def _build_ui(self):
        self.heading = tk.Label(self.root, text="UI ALERT MACRO v5.2", font=("Segoe UI", 18, "bold"))
        self.heading.pack(pady=(12, 9))
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.main_page = tk.Frame(self.notebook)
        self.settings_page = tk.Frame(self.notebook)
        self.developer_page = tk.Frame(self.notebook)
        self.credits_page = tk.Frame(self.notebook)
        self.notebook.add(self.main_page, text="Main")
        self.notebook.add(self.settings_page, text="Settings and Other")
        self.notebook.add(self.credits_page, text="Credits")
        self.notebook.bind("<<NotebookTabChanged>>", self._main_tab_changed)
        self._build_main()
        self._build_settings()
        self._build_developer()
        self._build_credits()
        self.root.bind_all("<MouseWheel>", self._wheel_scroll, add="+")

    def _build_main(self):
        self.tabstrip_holder = tk.Frame(self.main_page)
        self.tabstrip_holder.pack(fill="x", padx=14, pady=(12, 6))
        self.scroll_left = tk.Button(self.tabstrip_holder, text="‹", width=2,
                                     command=lambda: self.tabstrip_canvas.xview_scroll(-4, "units"))
        self.scroll_left.pack(side="left")
        self.scroll_right = tk.Button(self.tabstrip_holder, text="›", width=2,
                                      command=lambda: self.tabstrip_canvas.xview_scroll(4, "units"))
        self.scroll_right.pack(side="right")
        self.tabstrip_canvas = tk.Canvas(self.tabstrip_holder, height=39, highlightthickness=0, bd=0)
        self.tabstrip_canvas.pack(side="left", fill="x", expand=True)
        self.tabstrip = tk.Frame(self.tabstrip_canvas)
        self.tabstrip_canvas.create_window((0, 0), window=self.tabstrip, anchor="nw")
        self.tabstrip.bind("<Configure>", lambda _event: self.tabstrip_canvas.configure(
            scrollregion=self.tabstrip_canvas.bbox("all")))
        self.workspace_panel = tk.Frame(self.main_page)
        self.workspace_panel.pack(fill="both", expand=True)
        color_row = tk.Frame(self.workspace_panel)
        color_row.pack(fill="x", padx=24, pady=(2, 0))
        self.color_btn = tk.Button(color_row, text="Color ▾", command=self._choose_color, font=("Segoe UI", 9))
        self.color_btn.pack(side="right")
        self.window_toggle = tk.Checkbutton(
            color_row, variable=self.window_enabled_var, command=self._toggle_window_enabled,
            font=("Segoe UI", 9))
        self.window_toggle.pack(side="right", padx=(0, 12))
        self.status_label = tk.Label(self.workspace_panel, textvariable=self.status_var, font=("Segoe UI", 14, "bold"))
        self.status_label.pack(pady=(12, 8))
        self.button_bar = tk.Frame(self.workspace_panel)
        self.button_bar.pack()
        self.start_btn = tk.Button(self.button_bar, width=17, height=2, command=lambda: self._run_current(True))
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = tk.Button(self.button_bar, width=17, height=2, command=lambda: self._run_current(False))
        self.stop_btn.pack(side="left", padx=6)
        self.all_hint = tk.Label(self.workspace_panel, font=("Segoe UI", 8))
        self.all_hint.pack(pady=(5, 1))
        self.vip_group = tk.LabelFrame(self.workspace_panel, padx=8, pady=8)
        self.vip_group.pack(fill="x", padx=22, pady=(12, 5))
        self.vip_entry = tk.Entry(self.vip_group, textvariable=self.vip_var, font=("Segoe UI", 9))
        self.vip_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._enable_paste(self.vip_entry)
        self.vip_entry.bind("<FocusOut>", lambda _e: self._save_vip(silent=True))
        self.area_btn = tk.Button(self.workspace_panel, width=35, command=self._toggle_overlay)
        self.area_btn.pack(pady=(12, 4))
        self.area_hint = tk.Label(self.workspace_panel, font=("Segoe UI", 9))
        self.area_hint.pack()
        self.region_label = tk.Label(self.workspace_panel, textvariable=self.region_var, font=("Consolas", 10))
        self.region_label.pack(pady=(7, 2))
        self.detect_label = tk.Label(self.workspace_panel, textvariable=self.detect_var, font=("Segoe UI", 10, "bold"))
        self.detect_label.pack(pady=(8, 0))
        self.score_label = tk.Label(self.workspace_panel, textvariable=self.score_var, font=("Segoe UI", 9))
        self.score_label.pack(pady=(2, 4))

    def _scrolling_page(self, parent):
        holder = tk.Frame(parent)
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(holder, highlightthickness=0, bd=0)
        bar = tk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas)
        win_id = canvas.create_window((0, 0), anchor="nw", window=body)
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))
        return canvas, body

    def _wheel_scroll(self, event):
        chosen = self.notebook.select()
        if chosen == str(self.settings_page):
            canv = self.settings_canvas
        elif chosen == str(self.developer_page) and self.config.get("developer"):
            canv = self.developer_canvas
        else:
            return None
        pointer = self.root.winfo_containing(event.x_root, event.y_root)
        cur = pointer
        inside = False
        while cur is not None:
            if cur == canv:
                inside = True
                break
            cur = getattr(cur, "master", None)
        if not inside:
            return None
        canv.yview_scroll(-1 * (1 if event.delta > 0 else -1), "units")
        return "break"

    def _build_settings(self):
        self.settings_canvas, body = self._scrolling_page(self.settings_page)
        self.webhook_group = tk.LabelFrame(body, padx=10, pady=8)
        self.webhook_group.pack(fill="x", padx=17, pady=(13, 6))
        self.webhook_entry = tk.Entry(self.webhook_group, textvariable=self.webhook_var, font=("Segoe UI", 9))
        self.webhook_entry.pack(fill="x")
        self._enable_paste(self.webhook_entry)

        self.roles_group = tk.LabelFrame(body, padx=10, pady=7)
        self.roles_group.pack(fill="x", padx=17, pady=6)
        self.roles_group.columnconfigure(2, weight=1)
        self.enabled_switches = {}
        self.role_entries = {}
        for idx, (key, (name, _files)) in enumerate(EVENTS.items()):
            toggle = tk.Checkbutton(self.roles_group, variable=self.enabled_vars[key],
                                    command=self._schedule_autosave, padx=0)
            toggle.grid(row=idx, column=0, padx=(0, 5), pady=3, sticky="w")
            self.enabled_switches[key] = toggle
            tk.Label(self.roles_group, text=name, anchor="w", width=24, font=("Segoe UI", 9)).grid(row=idx, column=1, padx=(0, 8), sticky="w", pady=3)
            entry = tk.Entry(self.roles_group, textvariable=self.role_vars[key], font=("Consolas", 9))
            entry.grid(row=idx, column=2, sticky="ew", pady=3)
            self._enable_paste(entry)
            self.role_entries[key] = entry
        self.roles_hint = tk.Label(self.roles_group, anchor="w", font=("Segoe UI", 8), justify="left")
        self.roles_hint.grid(row=len(EVENTS), column=0, columnspan=3, pady=(8, 2), sticky="w")

        cols = tk.Frame(body)
        cols.pack(fill="x", padx=17, pady=(7, 4))
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)
        self.language_group = tk.LabelFrame(cols, padx=8, pady=7)
        self.language_group.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        self.lang_en = tk.Radiobutton(self.language_group, variable=self.language_var, value="en", command=self._preview_language)
        self.lang_en.pack(side="left", padx=(0, 12))
        self.lang_ru = tk.Radiobutton(self.language_group, variable=self.language_var, value="ru", command=self._preview_language)
        self.lang_ru.pack(side="left")
        self.theme_group = tk.LabelFrame(cols, padx=8, pady=7)
        self.theme_group.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        self.light_radio = tk.Radiobutton(self.theme_group, variable=self.theme_var, value="light", command=self._preview_theme)
        self.light_radio.pack(side="left", padx=(0, 12))
        self.dark_radio = tk.Radiobutton(self.theme_group, variable=self.theme_var, value="dark", command=self._preview_theme)
        self.dark_radio.pack(side="left")

        self.screenshot_group = tk.LabelFrame(body, padx=10, pady=9)
        self.screenshot_group.pack(fill="x", padx=17, pady=(7, 6))
        self.crop_checkbox = tk.Checkbutton(self.screenshot_group, variable=self.crop_var, command=self._refresh_crop_option)
        self.crop_checkbox.pack(anchor="w", pady=3)
        self.margin_checkbox = tk.Checkbutton(self.screenshot_group, variable=self.margin_var)
        self.margin_checkbox.pack(anchor="w", padx=(18, 0), pady=3)
        self._refresh_crop_option()

        self.reset_btn = tk.Button(body, command=self._reset_settings, width=30)
        self.reset_btn.pack(pady=(0, 14))
        self.dev_group = tk.LabelFrame(body, padx=10, pady=10)
        self.dev_group.pack(fill="x", padx=17, pady=(7, 18))
        self.dev_checkbox = tk.Checkbutton(self.dev_group, variable=self.dev_var, command=self._toggle_developer)
        self.dev_checkbox.pack(anchor="w")
        self.dev_warning = tk.Label(self.dev_group, justify="left", anchor="w", wraplength=660, font=("Segoe UI", 9))
        self.dev_warning.pack(fill="x", padx=(4, 0), pady=(8, 1))

    def _build_developer(self):
        self.developer_canvas, body = self._scrolling_page(self.developer_page)
        self.threshold_group = tk.LabelFrame(body, padx=10, pady=8)
        self.threshold_group.pack(fill="x", padx=16, pady=(15, 10))
        self.threshold_group.columnconfigure(1, weight=1)
        self.threshold_label = tk.Label(self.threshold_group, text="", anchor="w")
        self.threshold_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 7))
        self.threshold_reset_buttons = []
        for idx, (key, (name, _)) in enumerate(EVENTS.items(), 1):
            tk.Label(self.threshold_group, text=name, width=23, anchor="w").grid(row=idx, column=0, padx=(0, 5), pady=4, sticky="w")
            tk.Label(self.threshold_group, text=f"({STANDARD_THRESHOLDS[key]:.2f})").grid(row=idx, column=1, sticky="w", pady=4)
            entry = tk.Entry(self.threshold_group, textvariable=self.threshold_vars[key], width=9, font=("Consolas", 9))
            entry.grid(row=idx, column=2, pady=4, padx=8)
            self._enable_paste(entry)
            btn = tk.Button(self.threshold_group, command=lambda k=key: self.threshold_vars[k].set(f"{STANDARD_THRESHOLDS[k]:.2f}"))
            btn.grid(row=idx, column=3, padx=(4, 0), sticky="e")
            self.threshold_reset_buttons.append(btn)
        self.gss_multi_checkbox = tk.Checkbutton(body, variable=self.gss_multi_var, anchor="w", justify="left")
        self.gss_multi_checkbox.pack(fill="x", padx=20, pady=(2, 14))
        self.quality_group = tk.LabelFrame(body, padx=10, pady=10)
        self.quality_group.pack(fill="x", padx=16, pady=(0, 10))
        self.global_quality_label = tk.Label(self.quality_group)
        self.global_quality_label.pack(anchor="w", pady=(2, 6))
        self.global_quality_box = ttk.Combobox(self.quality_group, textvariable=self.quality_var,
                                               values=list(QUALITY_HEIGHT), state="readonly", width=18)
        self.global_quality_box.pack(anchor="w", pady=(0, 12))
        self.biome_quality_label = tk.Label(self.quality_group)
        self.biome_quality_label.pack(anchor="w", pady=(0, 8))
        for key, (name, _) in EVENTS.items():
            row = tk.Frame(self.quality_group)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=name, width=25, anchor="w").pack(side="left")
            ttk.Combobox(row, textvariable=self.biome_quality_vars[key],
                         values=["global", *QUALITY_HEIGHT], state="readonly", width=16).pack(side="left")


    def _build_credits(self):
        self.credits_header = tk.Label(self.credits_page, text="UI ALERT MACRO v5.2", font=("Segoe UI", 18, "bold"))
        self.credits_header.pack(pady=(46, 5))
        self.credits_by = tk.Label(self.credits_page, font=("Segoe UI", 10))
        self.credits_by.pack(pady=(0, 18))
        self.credit_cards = []
        for name, discord in (("Kizmum", "mindustry"), ("Fonar", "nikline_")):
            card = tk.Frame(self.credits_page, bd=1, relief="solid")
            card.pack(fill="x", padx=118, pady=6)
            tk.Label(card, text=name, font=("Segoe UI", 12, "bold")).pack(pady=(10, 2))
            tk.Label(card, text=f"Discord: {discord}", font=("Consolas", 10)).pack(pady=(0, 10))
            self.credit_cards.append(card)
        self.credits_thanks = tk.Label(self.credits_page, font=("Segoe UI", 9))
        self.credits_thanks.pack(pady=20)

    def _refresh_tabstrip(self):
        for widget in self.tabstrip.winfo_children():
            widget.destroy()
        self.workspace_tab_widgets = []
        for window in self.windows:
            window_id = window["id"]
            selected = window_id == self.active_id
            container = tk.Frame(self.tabstrip, bd=1, relief="solid", highlightthickness=2 if selected else 1,
                                 highlightbackground=window["color"])
            container.pack(side="left", padx=(0, 4))
            button = tk.Button(container, text=window["name"][:14], width=12,
                               command=lambda wid=window_id: self._select_window(wid), relief="flat", bd=0)
            button.pack(side="left", padx=(3, 0), pady=2)
            switch = tk.Button(container, width=3, relief="flat", bd=0,
                               command=lambda wid=window_id: self._toggle_window_enabled(wid))
            switch.pack(side="left", padx=(0, 1), pady=2)
            close_button = None
            if len(self.windows) > 1:
                close_button = tk.Button(container, text="×", width=2, relief="flat", bd=0,
                                         command=lambda wid=window_id: self._remove_window(wid))
                close_button.pack(side="left", padx=(0, 2))
                close_button.pack_forget()
                def reveal(_event, btn=close_button):
                    if btn.winfo_exists():
                        btn.pack(side="left", padx=(0, 2))
                def hide(_event, frame=container, btn=close_button):
                    if not btn.winfo_exists():
                        return
                    x, y = frame.winfo_pointerxy()
                    if not (frame.winfo_rootx() <= x < frame.winfo_rootx() + frame.winfo_width() and
                            frame.winfo_rooty() <= y < frame.winfo_rooty() + frame.winfo_height()):
                        btn.pack_forget()
                for w in (container, button, switch, close_button):
                    w.bind("<Enter>", reveal, add="+")
                    w.bind("<Leave>", hide, add="+")
            self.workspace_tab_widgets.append((container, button, close_button, switch, window))
        self.add_button = tk.Button(self.tabstrip, text="+", width=3, command=self._add_window)
        self.add_button.pack(side="left", padx=(2, 0))
        self._color_tabstrip()
        self.root.after_idle(self._update_tabstrip_scrollregion)

    def _update_tabstrip_scrollregion(self):
        if self.tabstrip.winfo_exists():
            self.tabstrip_canvas.configure(scrollregion=self.tabstrip_canvas.bbox("all"))

    def _color_tabstrip(self):
        theme = self._effective_theme()
        palette = THEMES[theme]
        for frame, btn, close, switch, window in getattr(self, "workspace_tab_widgets", []):
            selected = window["id"] == self.active_id
            enabled = window.get("enabled", True)
            bg = (palette["tab_active"] if selected else palette["tab"]) if enabled else (
                "#51545a" if theme == "dark" else "#b7b9bd")
            fg = palette["fg"] if enabled else ("#a1a5ab" if theme == "dark" else "#64666c")
            frame.configure(bg=bg, highlightbackground=window["color"], highlightcolor=window["color"])
            btn.configure(bg=bg, fg=fg, activebackground=palette["active"], activeforeground=palette["fg"])
            switch.configure(text="●" if enabled else "○", bg=bg, fg=fg,
                             activebackground=palette["active"], activeforeground=palette["fg"])
            if close is not None:
                close.configure(bg=bg, fg=fg,
                                activebackground=palette["active"], activeforeground=palette["fg"])

    def _create_overlay(self, window: dict):
        wid = window["id"]
        self.overlay_map[wid] = RegionOverlay(
            self.root, window["region"],
            lambda region, save, ident=wid: self._region_changed(ident, region, save),
            self.t("overlay_text"), window["color"])
        self.overlay_map[wid].hide()

    def _region_changed(self, window_id: str, region: dict, save: bool):
        with self.lock:
            window = self._get_window(window_id)
            if window is None:
                return
            window["region"] = normalize_region(region)
        if self.active_id == window_id:
            self._update_region()
        if save:
            self._save()

    def _update_region(self):
        w = self._get_window()
        if w is None:
            return
        r = w["region"]
        self.region_var.set(f"X1={r['left']}  Y1={r['top']}   X2={r['left'] + r['width']}  Y2={r['top'] + r['height']}   {r['width']}x{r['height']}")

    def _select_window(self, window_id: str):
        if window_id == self.active_id:
            return
        self._save_vip(silent=True)
        self.active_id = window_id
        self._refresh_tabstrip()
        self._sync_active_display()
        self._refresh_overlay_visibility()
        self._apply_theme_for_tab()

    def _add_window(self):
        if len(self.windows) >= MAX_WINDOWS:
            messagebox.showinfo(self.t("info"), self.t("maximum"))
            return
        self._save_vip(silent=True)
        with self.lock:
            used = {w["name"] for w in self.windows}
            index = 2
            while f"Window {index}" in used:
                index += 1
            window = default_window(index)
            self.windows.append(window)
        self._create_overlay(window)
        self.active_id = window["id"]
        self._save()
        self._refresh_tabstrip()
        self._sync_active_display()
        self._refresh_overlay_visibility()
        self._apply_theme_for_tab()

    def _remove_window(self, window_id: str):
        if len(self.windows) <= 1:
            return
        if not messagebox.askyesno(self.t("info"), self.t("remove_window")):
            return
        if window_id == self.active_id:
            self._save_vip(silent=True)
        with self.lock:
            old = self._get_window(window_id)
            if old is None:
                return
            idx = self.windows.index(old)
            self.windows.remove(old)
            self.next_checks.pop(window_id, None)
            self.next_tgss_legacy.pop(window_id, None)
            self.next_tgss_fast.pop(window_id, None)
            self.tgss_suspect_until.pop(window_id, None)
            self.view_results.pop(window_id, None)
            self.cooldowns.remove_window(window_id)
        overlay = self.overlay_map.pop(window_id, None)
        if overlay:
            overlay.destroy()
        if self.active_id == window_id:
            self.active_id = self.windows[min(idx, len(self.windows) - 1)]["id"]
        self._save()
        self._refresh_tabstrip()
        self._sync_active_display()
        self._refresh_overlay_visibility()
        self._apply_theme_for_tab()

    def _toggle_window_enabled(self, window_id: str | None = None):
        window = self._get_window(window_id)
        if window is None:
            return
        enabled = (self.window_enabled_var.get() if window_id is None
                   else not window.get("enabled", True))
        with self.lock:
            window["enabled"] = bool(enabled)
            if not enabled:
                window["running"] = False
                self.next_checks.pop(window["id"], None)
        if window["id"] == self.active_id:
            self._sync_active_display()
        self._refresh_tabstrip()
        self._refresh_overlay_visibility()
        self._save()

    def _choose_color(self):
        window = self._get_window()
        if not window:
            return
        chosen = colorchooser.askcolor(initialcolor=window["color"], title=self.t("choose_color"), parent=self.root)
        if not chosen or not chosen[1]:
            return
        with self.lock:
            window["color"] = chosen[1]
        self.overlay_map[window["id"]].set_color(chosen[1])
        self._save()
        self._refresh_tabstrip()
        self._apply_theme_for_tab()

    def _sync_active_display(self):
        window = self._get_window()
        if not window:
            return
        self.vip_var.set(window["vip_url"])
        self.window_enabled_var.set(window.get("enabled", True))
        self.status_var.set(self.t("disabled") if not window.get("enabled", True) else (
            self.t("running") if window["running"] else self.t("stopped")))
        self._update_region()
        d, s = self.view_results.get(window["id"], (f"{self.t('last')}: —", f"{self.t('match')}: —"))
        self.detect_var.set(d)
        self.score_var.set(s)
        self._refresh_area_button()
        self._refresh_status_color()

    def _refresh_status_color(self):
        w = self._get_window()
        color = ("#38b858" if self._effective_theme() == "dark" else "#087a08") if w and w["running"] else ("#ff6b6b" if self._effective_theme() == "dark" else "#a00000")
        self.status_label.configure(fg=color)

    def _save_vip(self, silent: bool = True) -> bool:
        value = self.vip_var.get().strip()
        if value and not value.startswith(("https://", "http://")):
            if not silent:
                messagebox.showwarning(self.t("vip"), self.t("bad_vip"))
            return False
        with self.lock:
            w = self._get_window()
            if w is None:
                return False
            w["vip_url"] = value
        self._save()
        return True

    def _toggle_overlay(self):
        window = self._get_window()
        if not window:
            return
        if window["running"]:
            messagebox.showinfo(self.t("info"), self.t("locked"))
            return
        with self.lock:
            window["overlay_shown"] = not window["overlay_shown"]
        self._save()
        self._refresh_overlay_visibility()
        self._refresh_area_button()

    def _refresh_area_button(self):
        w = self._get_window()
        if not w:
            return
        self.area_btn.configure(text=self.t("area_hide") if w["overlay_shown"] and not w["running"] else self.t("area_show"))

    def _refresh_overlay_visibility(self):
        # Overlays remain visible when switching workspaces and top-level pages.
        # Running windows still hide their overlays so capture does not include them.
        for w in self.windows:
            overlay = self.overlay_map.get(w["id"])
            if not overlay:
                continue
            if w.get("enabled", True) and not w["running"] and w["overlay_shown"]:
                overlay.show()
            else:
                overlay.hide()
        active_overlay = self.overlay_map.get(self.active_id)
        if active_overlay is not None and active_overlay.visible():
            active_overlay.show()
        self._refresh_area_button()

    def _refresh_crop_option(self):
        self.margin_checkbox.configure(state="normal" if self.crop_var.get() else "disabled")

    def _validate_settings(self, running: bool = False) -> tuple[bool, str]:
        webhook = self.webhook_var.get().strip()
        if webhook and not is_valid_webhook(webhook):
            return False, self.t("bad_webhook")
        if running and (not is_valid_webhook(webhook) or
                        not any(v.get() and self.enabled_vars[key].get() for key, v in self.role_vars.items())):
            return False, self.t("missing_discord")
        if running:
            for var in self.threshold_vars.values():
                try:
                    v = float(var.get())
                    if not 0.01 <= v <= 1.0:
                        raise ValueError
                except ValueError:
                    return False, "Thresholds must be numbers between 0.01 and 1.00."
        return True, ""

    def _save_settings(self, silent: bool = False, running: bool = False) -> bool:
        if running:
            valid, reason = self._validate_settings(running=True)
            if not valid:
                if not silent:
                    messagebox.showerror(self.t("error"), reason)
                return False
        with self.lock:
            self.config["webhook_url"] = self.webhook_var.get().strip()
            self.config["role_ids"] = {key: digits(var.get()) for key, var in self.role_vars.items()}
            self.config["biome_enabled"] = {
                key: bool(self.enabled_vars[key].get()) and bool(self.config["role_ids"][key])
                for key in EVENTS
            }
            self.config["language"] = self.language_var.get()
            self.config["theme"] = self.theme_var.get()
            self.config["crop_only"] = self.crop_var.get()
            self.config["crop_margin"] = self.margin_var.get()
            self.config["developer"] = self.dev_var.get()
            self.config["gss_multi_ping"] = self.gss_multi_var.get()
            self.config["global_quality"] = self.quality_var.get()
            for key, var in self.threshold_vars.items():
                try:
                    value = float(var.get())
                    if 0.01 <= value <= 1.0:
                        self.config["thresholds"][key] = value
                except ValueError:
                    pass
            self.config["biome_quality"] = {key: var.get() for key, var in self.biome_quality_vars.items()}
            window = self._get_window()
            if window is not None:
                window["vip_url"] = self.vip_var.get().strip()
        self._save()
        return True

    def _reset_settings(self):
        if not messagebox.askyesno(self.t("info"), self.t("reset_confirm")):
            return
        # Webhook, role IDs and every window's VIP URL are deliberately preserved.
        default = default_config()
        with self.lock:
            keep_webhook = self.webhook_var.get()
            keep_roles = {key: digits(v.get()) for key, v in self.role_vars.items()}
            self.config.update({key: deepcopy(value) for key, value in default.items() if key not in ("windows", "webhook_url", "role_ids")})
            self.config["webhook_url"] = keep_webhook
            self.config["role_ids"] = keep_roles
            self.config["biome_enabled"] = {key: bool(keep_roles.get(key)) for key in EVENTS}
            for w in self.windows:
                w["color"] = default["windows"][0]["color"]
                w["region"] = deepcopy(DEFAULT_REGION)
                w["overlay_shown"] = True
                w["enabled"] = True
                overlay = self.overlay_map.get(w["id"])
                if overlay:
                    overlay.set_region(w["region"])
                    overlay.set_color(w["color"])
        for key in EVENTS:
            self.enabled_vars[key].set(bool(keep_roles.get(key)))
        self.language_var.set("en")
        self.theme_var.set("light")
        self.crop_var.set(False)
        self.margin_var.set(True)
        self.dev_var.set(False)
        self.gss_multi_var.set(True)
        self.quality_var.set("1080p")
        for key in EVENTS:
            self.threshold_vars[key].set(f"{STANDARD_THRESHOLDS[key]:.2f}")
            self.biome_quality_vars[key].set("global")
        self._refresh_crop_option()
        self._update_developer_tab()
        self._save_settings(silent=True)
        self._apply_language()
        self._refresh_tabstrip()
        self._sync_active_display()
        self._apply_theme_for_tab()
        self._refresh_overlay_visibility()

    def _toggle_developer(self):
        self._update_developer_tab()
        self._save_settings(silent=True)

    def _update_developer_tab(self):
        all_tabs = self.notebook.tabs()
        exists = str(self.developer_page) in all_tabs
        enabled = self.dev_var.get()
        if enabled and not exists:
            self.notebook.insert(2, self.developer_page, text=self.t("developer"))
        if not enabled and exists:
            if self.notebook.select() == str(self.developer_page):
                self.notebook.select(self.settings_page)
            self.notebook.forget(self.developer_page)
        self._apply_language()

    def _preview_language(self):
        self._apply_language()
        self._apply_theme_for_tab()
        self._schedule_autosave()

    def _preview_theme(self):
        self._apply_theme_for_tab()
        self._schedule_autosave()

    def _apply_language(self):
        self.notebook.tab(self.main_page, text=self.t("main"))
        self.notebook.tab(self.settings_page, text=self.t("settings"))
        self.notebook.tab(self.credits_page, text=self.t("credits"))
        if str(self.developer_page) in self.notebook.tabs():
            self.notebook.tab(self.developer_page, text=self.t("developer"))
        for widget, key in ((self.start_btn, "start"), (self.stop_btn, "stop"), (self.all_hint, "all_hint"),
                            (self.vip_group, "vip"), (self.area_hint, "area_hint"),
                            (self.webhook_group, "webhook"), (self.roles_group, "roles"), (self.roles_hint, "roles_hint"),
                            (self.language_group, "language"), (self.theme_group, "theme"),
                            (self.lang_en, "english"), (self.lang_ru, "russian"),
                            (self.light_radio, "light"), (self.dark_radio, "dark"),
                            (self.screenshot_group, "screenshot_options"), (self.crop_checkbox, "crop_only"),
                            (self.margin_checkbox, "crop_margin"), (self.window_toggle, "window_on"),
                            (self.reset_btn, "reset"), (self.dev_group, "dev_enable"),
                            (self.dev_checkbox, "dev_enable"), (self.dev_warning, "dev_warning"),
                            (self.threshold_group, "dev_thresholds"), (self.quality_group, "dev_quality"),
                            (self.global_quality_label, "global_quality"), (self.biome_quality_label, "per_biome"),
                            (self.gss_multi_checkbox, "gss_multi"),
                            (self.credits_by, "credits_by"),
                            (self.credits_thanks, "credits_thanks")):
            widget.configure(text=self.t(key))
        self.threshold_label.configure(text=f"{self.t('standard')}: 0.66")
        self.color_btn.configure(text=("Color ▾" if self.language_var.get() == "en" else "Цвет ▾"))
        for btn in self.threshold_reset_buttons:
            btn.configure(text=self.t("reset_one"))
        for overlay in self.overlay_map.values():
            overlay.set_text(self.t("overlay_text"))
        self._sync_active_display()

    def _effective_theme(self) -> str:
        selected = self.notebook.select() if hasattr(self, "notebook") else ""
        theme = self.theme_var.get()
        if selected == str(self.credits_page):
            return "light" if theme == "dark" else "dark"
        return theme

    def _main_tab_changed(self, _event=None):
        self._refresh_overlay_visibility()
        self._apply_theme_for_tab()

    def _apply_theme_for_tab(self):
        name = self._effective_theme()
        p = THEMES[name]
        self.root.configure(bg=p["bg"])
        self.style.configure("TNotebook", background=p["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=p["tab"], foreground=p["fg"], padding=(14, 7))
        self.style.map("TNotebook.Tab", background=[("selected", p["tab_active"]), ("active", p["active"])],
                       foreground=[("selected", p["fg"])])
        self.style.configure("TCombobox", fieldbackground=p["entry"], background=p["button"], foreground=p["fg"])
        self.style.map("TCombobox", fieldbackground=[("readonly", p["entry"])], foreground=[("readonly", p["fg"])])
        self._theme_tree(self.root, p)
        for card in self.credit_cards:
            card.configure(bg="#1c1f24" if name == "dark" else p["panel"])
            for child in card.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=card.cget("bg"), fg=p["fg"])
        self.dev_warning.configure(fg="#ff7676" if name == "dark" else "#c02020")
        self.roles_hint.configure(fg=p["muted"])
        self.all_hint.configure(fg=p["muted"])
        self._color_tabstrip()
        self.color_btn.configure(highlightbackground=self._get_window()["color"] if self._get_window() else p["border"])
        self._refresh_status_color()

    def _theme_tree(self, parent, palette: dict):
        for child in parent.winfo_children():
            if isinstance(child, tk.Toplevel):
                continue
            try:
                if isinstance(child, tk.LabelFrame):
                    child.configure(bg=palette["panel"], fg=palette["fg"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=palette["panel"])
                elif isinstance(child, tk.Label):
                    child.configure(bg=palette["panel"], fg=palette["fg"])
                elif isinstance(child, tk.Entry):
                    child.configure(bg=palette["entry"], fg=palette["fg"], insertbackground=palette["fg"], relief="solid", bd=1)
                elif isinstance(child, tk.Button):
                    child.configure(bg=palette["button"], fg=palette["fg"], activebackground=palette["active"],
                                    activeforeground=palette["fg"])
                elif isinstance(child, (tk.Radiobutton, tk.Checkbutton)):
                    child.configure(bg=palette["panel"], fg=palette["fg"], selectcolor=palette["entry"],
                                    activebackground=palette["panel"], activeforeground=palette["fg"])
                elif isinstance(child, tk.Canvas):
                    child.configure(bg=palette["panel"])
            except tk.TclError:
                pass
            self._theme_tree(child, palette)

    def _check_start_settings(self) -> bool:
        if not self.templates:
            messagebox.showerror(self.t("error"), self.t("missing_templates"))
            return False
        if not self._save_settings(silent=True, running=True):
            _valid, why = self._validate_settings(running=True)
            messagebox.showerror(self.t("error"), why)
            return False
        return self._save_vip(silent=False)

    def _set_window_running(self, window_id: str, state: bool):
        with self.lock:
            window = self._get_window(window_id)
            if window is None:
                return
            if state and not window.get("enabled", True):
                return
            if state and not window["running"]:
                self.next_checks[window_id] = 0.0
                self.next_tgss_legacy[window_id] = 0.0
                self.next_tgss_fast[window_id] = 0.0
                self.tgss_suspect_until.pop(window_id, None)
            window["running"] = state
        if window_id == self.active_id:
            self._sync_active_display()
        self._refresh_overlay_visibility()

    def _run_current(self, state: bool):
        if state and not self._get_window().get("enabled", True):
            return
        if state and not self._check_start_settings():
            return
        self._set_window_running(self.active_id, state)

    def _run_all(self, state: bool):
        if state and not any(w.get("enabled", True) for w in self.windows):
            return
        if state and not self._check_start_settings():
            return
        for window in list(self.windows):
            self._set_window_running(window["id"], state)

    def _check_hotkeys(self):
        if self.shutdown.is_set():
            return
        if key_pressed(VK_F1):
            self._run_all(True)
        if key_pressed(VK_F2):
            self._run_all(False)
        self.root.after(45, self._check_hotkeys)

    def _drain_queue(self):
        if self.shutdown.is_set():
            return
        for _ in range(80):
            try:
                window_id, title, detail = self.messages.get_nowait()
            except queue.Empty:
                break
            if self._get_window(window_id) is None:
                continue
            self.view_results[window_id] = (title, detail)
            if window_id == self.active_id:
                self.detect_var.set(title)
                self.score_var.set(detail)
        self.root.after(100, self._drain_queue)

    def _make_tgss_diagnostics(self, shot: np.ndarray, cfg: dict, enabled_keys: set[str], trigger: str) -> dict:
        # Both engines evaluate the EXACT frame that caused the alert.
        return {
            "trigger": trigger,
            "modern": detect_event(shot, self.templates, cfg["thresholds"], enabled_keys),
            "modern_tgss_score": modern_tgss_score(shot, self.templates[TGSS_KEY]),
            "modern_threshold": float(cfg["thresholds"].get(TGSS_KEY, STANDARD_THRESHOLDS[TGSS_KEY])),
            "legacy": detect_tgss_legacy(shot, self.legacy_templates),
        }

    def _deliver_alert(self, sct: mss.mss, window: dict, cfg: dict, shot: np.ndarray,
                       enabled_keys: set[str], event_key: str, trigger: str, title: str) -> None:
        wid = window["id"]
        role_id = digits(cfg["role_ids"].get(event_key, ""))
        if not role_id:
            return
        with self.lock:
            if self.cooldowns.remaining(wid, event_key, time.monotonic()) > 0:
                return
            current = self._get_window(wid)
            if not current or not current["running"] or not current.get("enabled", True):
                return
            if not self.config["biome_enabled"].get(event_key, False):
                return
            if self.config["role_ids"].get(event_key) != role_id:
                return
        if not is_valid_webhook(cfg["webhook_url"]):
            self.messages.put((wid, title, "Invalid Discord webhook URL"))
            return
        diagnostics = None
        if EXPERIMENTAL and event_key == TGSS_KEY:
            diagnostics = self._make_tgss_diagnostics(shot, cfg, enabled_keys, trigger)
        image, filename = screenshot_jpeg(sct, window["region"], cfg, event_key)
        sent, message = send_discord_ping(event_key, role_id, cfg["webhook_url"],
                                          window["vip_url"], image, filename, diagnostics)
        self.messages.put((wid, title, message))
        if sent:
            completed_at = time.monotonic()
            with self.lock:
                self.cooldowns.record_success(wid, event_key, completed_at, cfg["gss_multi_ping"])
        if EXPERIMENTAL and event_key == TGSS_KEY:
            print(f"[TGSS EX] Sent={sent} Trigger={trigger} "
                  f"Modern={diagnostics['modern_tgss_score']:.3f} "
                  f"Legacy={diagnostics['legacy'].tgss_score:.3f}", flush=True)

    def _monitor_loop(self):
        try:
            with mss.mss() as sct:
                while not self.shutdown.is_set():
                    with self.lock:
                        active = [deepcopy(w) for w in self.windows if w["running"] and w.get("enabled", True)]
                        cfg = deepcopy(self.config)
                    if not active:
                        time.sleep(0.1)
                        continue
                    enabled_keys = {
                        key for key in EVENTS
                        if cfg["biome_enabled"].get(key, False) and digits(cfg["role_ids"].get(key, ""))
                    }
                    for window in active:
                        if self.shutdown.is_set():
                            break
                        wid = window["id"]
                        now = time.monotonic()
                        base_due = now >= self.next_checks.get(wid, 0.0)
                        # Legacy TGSS is a separate 2.5-second clock; other biomes remain at 5 seconds.
                        gss_enabled = TGSS_KEY in enabled_keys and bool(self.legacy_templates)
                        if gss_enabled:
                            with self.lock:
                                gss_cooling = self.cooldowns.remaining(wid, TGSS_KEY, now) > 0
                        else:
                            gss_cooling = True
                        legacy_due = (not gss_cooling and
                                      now >= self.next_tgss_legacy.get(wid, 0.0))
                        fast_due = (not gss_cooling and
                                    now < self.tgss_suspect_until.get(wid, 0.0) and
                                    now >= self.next_tgss_fast.get(wid, 0.0))
                        if not (base_due or legacy_due or fast_due):
                            continue
                        if base_due:
                            self.next_checks[wid] = now + CHECK_INTERVAL
                        if legacy_due:
                            self.next_tgss_legacy[wid] = now + TGSS_LEGACY_INTERVAL
                        if fast_due:
                            self.next_tgss_fast[wid] = now + TGSS_FAST_INTERVAL
                        if not enabled_keys:
                            continue
                        try:
                            shot = capture_region(sct, window["region"])
                            result = None
                            trigger = None
                            title = ""
                            # Existing v5.2 full scan is preserved verbatim at 5-second intervals.
                            if base_due:
                                result = detect_event(shot, self.templates, cfg["thresholds"], enabled_keys)
                                name = EVENTS[result.best_key][0]
                                title = (f"{self.t_name('last', cfg)}: {name}" if result.event_key
                                         else f"{self.t_name('looks_like', cfg)}: {name}, {self.t_name('not_confirmed', cfg)}")
                                detail = (f"{self.t_name('match', cfg)}: {result.score:.3f}   "
                                          f"{self.t_name('second', cfg)}: {result.second_score:.3f}   "
                                          f"{self.t_name('threshold', cfg)}: {result.threshold:.2f}")
                                self.messages.put((wid, title, detail))
                                if result.event_key:
                                    trigger = "Modern (standard 5s scan)"
                            if not gss_cooling:
                                tgss_score = None
                                # Fast scans touch ONLY TGSS references. A promising match is
                                # verified against all biomes before any notification.
                                if base_due or fast_due:
                                    tgss_score = modern_tgss_score(shot, self.templates[TGSS_KEY])
                                    threshold = float(cfg["thresholds"].get(TGSS_KEY, 0.66))
                                    if EXPERIMENTAL:
                                        print(f"[TGSS EX] window={wid} modern={tgss_score:.3f} "
                                              f"threshold={threshold:.3f} "
                                              f"scan={'5s' if base_due else '0.75s'}", flush=True)
                                    if tgss_is_suspected(tgss_score, threshold):
                                        was_suspected = self.tgss_suspect_until.get(wid, 0.0) > now
                                        self.tgss_suspect_until[wid] = now + TGSS_SUSPECT_DURATION
                                        if not was_suspected:
                                            self.next_tgss_fast[wid] = now + TGSS_FAST_INTERVAL
                                    elif fast_due:
                                        # Stop accelerated sampling when it no longer resembles TGSS.
                                        self.tgss_suspect_until.pop(wid, None)
                                    if fast_due and not base_due and tgss_score >= threshold and trigger is None:
                                        confirmed = detect_event(shot, self.templates, cfg["thresholds"], enabled_keys)
                                        if confirmed.event_key == TGSS_KEY:
                                            result = confirmed
                                            trigger = "Modern (adaptive 0.75s scan)"
                                            title = f"{self.t_name('last', cfg)}: {EVENTS[TGSS_KEY][0]}"
                                if legacy_due:
                                    legacy = detect_tgss_legacy(shot, self.legacy_templates)
                                    if EXPERIMENTAL:
                                        print(f"[TGSS EX] window={wid} legacy={legacy.tgss_score:.3f} "
                                              f"best={legacy.best_key} second={legacy.second_score:.3f} "
                                              f"pass={legacy.detected}", flush=True)
                                    if legacy.detected:
                                        was_suspected = self.tgss_suspect_until.get(wid, 0.0) > now
                                        self.tgss_suspect_until[wid] = now + TGSS_SUSPECT_DURATION
                                        if not was_suspected:
                                            self.next_tgss_fast[wid] = now + TGSS_FAST_INTERVAL
                                        if trigger is None:
                                            result = DetectionResult(TGSS_KEY, TGSS_KEY, legacy.tgss_score,
                                                                     legacy.second_score, legacy.threshold)
                                            trigger = "Legacy v2 (2.5s scan)"
                                            title = f"{self.t_name('last', cfg)}: {EVENTS[TGSS_KEY][0]}"
                            if trigger is None or result is None or result.event_key is None:
                                continue
                            self._deliver_alert(sct, window, cfg, shot, enabled_keys,
                                                result.event_key, trigger, title)
                        except Exception as exc:
                            self.messages.put((wid, "Error", str(exc)))
                    time.sleep(0.05)
        except Exception as exc:
            self.messages.put((self.active_id, "Monitor error", str(exc)))

    @staticmethod
    def t_name(key: str, cfg: dict) -> str:
        return I18N.get(cfg.get("language", "en"), I18N["en"]).get(key, key)

    def _close(self):
        if self._autosave_job is not None:
            self.root.after_cancel(self._autosave_job)
            self._autosave_job = None
        self._save_settings(silent=True)
        self.shutdown.set()
        with self.lock:
            for window in self.windows:
                window["running"] = False
        try:
            self._save()
        except OSError:
            pass
        for overlay in self.overlay_map.values():
            overlay.destroy()
        self.root.destroy()


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
