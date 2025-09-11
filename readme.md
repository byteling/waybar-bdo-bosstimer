# waybar-bdo-bosstimer

This is a script to add the upcoming bdo boss encounters to your waybar.

## Installation

Place bdo-bosstimer.py and timers.json in a directory of your choice.

Add the following to your module section of `~/.config/waybar/config.jsonc`:

```jsonc
    "custom/bdo-bosses": {
      "exec": "full/path/to/bdo-bosstimer.py",
      "interval": 0,
      "on-click": "",
      "format": "{}",
      "return-type": "json",
    },
```

Then add `custom/bdo-bosses` where you like in the `modules-*` section.

## Todo

- alarms?
- disable specific bosses?
- the same but without editing the json manually?
