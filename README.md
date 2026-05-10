# SMS Gateway Notify (HACS)

Home Assistant custom integration that adds a `notify` service backed by your SMS gateway API.

## Features
- Config Flow (UI setup)
- Ask for:
  - Gateway URL/IP (example: `http://192.168.200.52:8091`)
  - API key (med `send` + `modem_status` scope)
  - Default recipient phone numbers (comma-separated)
- Uses Home Assistant notify service with optional per-message targets

## Install via HACS (custom repository)
1. Push this repo to GitHub.
2. In Home Assistant -> HACS -> Integrations -> top-right menu -> Custom repositories.
3. Add repo URL and category **Integration**.
4. Install **SMS Gateway Notify**.
5. Restart Home Assistant.
6. Add integration in Settings -> Devices & Services.

## Usage
After setup, call notify service from automations/scripts.

Use default recipients from integration config:
```yaml
action:
  - service: notify.sms_gateway_notify
    data:
      message: "Varsel fra Home Assistant"
```

Override recipients for one message:
```yaml
action:
  - service: notify.sms_gateway_notify
    data:
      message: "Kun til denne mottakeren"
      target:
        - "40038021"
```

## Requirements on gateway side
- Endpoint: `POST /api/external/send`
- Header: `X-API-Key`
- JSON payload: `{ "number": "40038021", "text": "..." }`
- API key must include `send` scope.
- Setup validation calls `/api/external/status`, so key should also include `modem_status` scope.

## Notes
- Phone number validation is done by gateway API.
- If no `target` is provided in notify call, integration uses configured default recipients.
