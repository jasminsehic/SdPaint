import json
from .utils import load_config, update_size, fetch_configuration


class State:
    """
        Store the current state of the application.
    """

    configuration = {
        "config_file": "config.json",
        "config": {},
        "webui_config": {}
    }
    presets = {
        "presets_file": "presets.json",
        "list": load_config("presets.json"),
        "fields": ["hr_enabled", "hr_scale", "hr_upscaler", "denoising_strength"],
    }
    server = {
        "url": 'http://127.0.0.1:7860',
        "busy": False,
    }
    render = {
        "checkpoint": None,
        "vae": None,
        "hr_scales": [],
        "hr_scale": 1.0,
        "hr_scale_prev": 1.25,
        "hr_upscalers": ['Latent (bicubic)'],
        "hr_upscaler": 'Latent (bicubic)',
        'denoising_strengths': [0.6],
        'denoising_strength': 0.6,
        "batch_sizes": [1, 4, 9, 16],
        "batch_size": 1,
        "batch_size_prev": 4,
        "batch_hr_scale_prev": 1.0,
        "clip_skip": 1,
        "width": 512,
        "height": 512,
        "soft_upscale": 1.0,
        "pixel_perfect": False,
        "use_invert_module": True,
        "quick_mode": False,
    }
    control_net = {
        "controlnet_models": [],
        "controlnet_model": None,
        "controlnet_weights": [0.6, 1.0, 1.6],
        "controlnet_guidance_ends": [1.0, 0.2, 0.3],
        "controlnet_guidance_end": 1.0,
        "preset_fields": ["controlnet_model", "controlnet_weight", "controlnet_guidance_end"],
    }
    samplers = {
        "list": ["DDIM"],
        "sampler": "DDIM",
    }
    detectors = {
        "list": ('lineart',),
        "detector": "lineart",
    }
    autosave = {
        "seed": False,
        "prompt": False,
        "negative_prompt": False,
        "images": False,
        "images_max": 5,
    }
    json_file = "controlnet.json"
    main_json_data = {}
    settings = {}
    img2img = ""
    gen_settings = {
        "seed": 3456456767,
        "prompt": "",
        "negative_prompt": "",
    }
    
    def __init__(self, img2img="#"):
        self.img2img = img2img
        self.update_config()
        self.update_settings()
    
    def update_config(self):
        """
            Update global configuration.
        """
        self.configuration["config"] = load_config("config.json")

        hr_scales = self.configuration["config"].get("hr_scales", [1.0, 1.25, 1.5, 2.0])
        if 1.0 not in hr_scales:
            hr_scales.insert(0, 1.0)
        hr_scale = hr_scales[0]

        self.render["hr_scale_prev"] = hr_scales[1]
        self.render["hr_upscalers"] = self.configuration["config"].get("hr_upscalers", ['Latent (bicubic)'])
        self.render["hr_upscaler"] = self.render["hr_upscalers"][0]
        self.render["denoising_strengths"] = self.configuration["config"].get("denoising_strengths", [0.6])
        self.render["denoising_strength"] = self.render["denoising_strengths"][0]

        self.samplers["list"] = self.configuration["config"].get("samplers", ["DDIM"])
        self.samplers["sampler"] = self.samplers["list"][0]

        self.detectors["list"] = self.configuration["config"].get('detectors', ('lineart',))
        self.detectors["detector"] = self.detectors["list"][0]

        self.control_net["controlnet_models"]: list[str] = self.configuration["config"].get("controlnet_models", [])
        self.control_net["controlnet_weights"] = self.configuration["config"].get("controlnet_weights", [0.6, 1.0, 1.6])
        self.control_net["controlnet_weight"] = self.control_net["controlnet_weights"][0]
        self.control_net["controlnet_guidance_ends"] = self.configuration["config"].get("controlnet_guidance_ends", [1.0, 0.2, 0.3])
        self.control_net["controlnet_guidance_end"] = self.control_net["controlnet_guidance_ends"][0]

        self.control_net["preset_fields"] = self.configuration["config"].get('cn_preset_fields', ["controlnet_model", "controlnet_weight", "controlnet_guidance_end"])
        self.presets["fields"] = self.configuration["config"].get('preset_fields', ["hr_enabled", "hr_scale", "hr_upscaler", "denoising_strength"])

        batch_sizes = self.configuration["config"].get("batch_sizes", [1, 4, 9, 16])
        if 1 not in batch_sizes:
            batch_sizes.insert(0, 1)
        self.render["batch_size"] = batch_sizes[0]
        self.render["batch_size_prev"] = batch_sizes[1]
        self.render["batch_hr_scale_prev"] = hr_scale
        self.render["batch_images"] = []
        self.render["hr_scales"] = hr_scales
        self.render["hr_scale"] = hr_scale
        self.render["batch_sizes"] = batch_sizes

        self.autosave["seed"] = self.configuration["config"].get('autosave_seed', 'false') == 'true'
        self.autosave["prompt"] = self.configuration["config"].get('autosave_prompt', 'false') == 'true'
        self.autosave["negative_prompt"] = self.configuration["config"].get('autosave_negative_prompt', 'false') == 'true'
        self.autosave["images"] = self.configuration["config"].get('autosave_images', 'false') == 'true'
        self.autosave["images_max"] = self.configuration["config"].get('autosave_images_max', 5)

        self.server["url"] = self.configuration["config"].get('url', 'http://127.0.0.1:7860')
    
    def update_settings(self):
        """
            Update rendering settings.
        """
        if self.img2img:
            self.json_file = "img2img.json"
        else:
            self.json_file = "controlnet.json"

        self.settings = load_config(self.json_file)
        settings = self.settings

        self.gen_settings["seed"] = settings.get('seed', 3456456767)
        if settings.get('override_settings', None) is not None and settings['override_settings'].get('CLIP_stop_at_last_layers', None) is not None:
            self.render["clip_skip"] = settings['override_settings']['CLIP_stop_at_last_layers']

        if settings.get('enable_hr', 'false') == 'true':
            self.render["hr_scale"] = self.render["hr_scales"][1]
            self.render["batch_hr_scale_prev"] = self.render["hr_scale"]

        self.gen_settings["prompt"] = settings.get('prompt', '')
        self.gen_settings["negative_prompt"] = settings.get('negative_prompt', '')

        if settings.get("controlnet_units", None) and settings.get("controlnet_units")[0].get('pixel_perfect', None):
            self.render["pixel_perfect"] = settings.get("controlnet_units")[0]["pixel_perfect"] == "true"
        else:
            self.render["pixel_perfect"] = False

        self.render["width"] = settings.get('width', 512)
        self.render["height"] = settings.get('height', 512)
        self.render["init_width"] = self.render["width"] * 1.0
        self.render["init_height"] = self.render["height"] * 1.0
        self.render["soft_upscale"] = 1.0
        if settings.get("controlnet_units", None) and settings.get("controlnet_units")[0].get('model', None):
            self.control_net["controlnet_model"] = settings.get("controlnet_units")[0]["model"]
        elif self.control_net["controlnet_models"]:
            self.control_net["controlnet_model"] = self.control_net["controlnet_models"][0]
        else:
            self.control_net["controlnet_model"] = None
        update_size(self)

        if self.control_net["controlnet_models"] and settings.get("controlnet_units", None) and not settings.get("controlnet_units")[0].get('model', None):
            settings['controlnet_units'][0]['model'] = self.control_net["controlnet_models"]
            with open(self.json_file, "w") as f:
                json.dump(settings, f, indent=4)

    def update_webui_config(self):
        """
            Update webui configuration from the API.
        """
        self.configuration["webui_config"] = fetch_configuration(self)
        self.render['checkpoint'] = self.configuration["webui_config"]['sd_model_checkpoint']
        self.render['vae'] = self.configuration["webui_config"]['sd_vae']

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)
