# SMS Gateway Notify (HACS)

Home Assistant custom integration that adds a `notify` service backed by your SMS gateway API.

## Features
- Config Flow (UI setup)
- Ask for:
  - Gateway URL/IP (example: `http://192.168.200.52:8091`)
  - API key
  - Default recipient phone numbers (comma-separated)
- Setup validation uses the status endpoint, so the API key should allow both `modem_status` and `send`
- Uses Home Assistant `notify.send_message` with one gateway entity + one entity per configured recipient
- Creates a diagnostic device/sensor for gateway status

## Install via HACS (custom repository)

Brand asset is expected at `brand/icon.png` in the repo root (and is also mirrored into the integration folder for Home Assistant UI branding).
1. Push this repo to GitHub.
2. In Home Assistant -> HACS -> Integrations -> top-right menu -> Custom repositories.
3. Add repo URL and category **Integration**.
4. Install **SMS Gateway Notify**.
5. Restart Home Assistant.
6. Add integration in Settings -> Devices & Services.

## Usage
After setup, use the Home Assistant service `notify.send_message` and target the SMS entities.

Send to the gateway default recipients:
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.sms_gateway_notify_gateway
    data:
      message: "Varsel fra Home Assistant"
```

Send to a specific number entity:
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.sms_gateway_notify_40038021
    data:
      message: "Kun til denne mottakeren"
```

If you add more phone numbers in the integration options, new notify entities are created for them.

If you change IP, API key, or recipients later, use the integration options (gear icon) to edit them.

## Requirements on gateway side
- Endpoint: `POST /api/external/send`
- Header: `X-API-Key`
- JSON payload: `{ "number": "40038021", "text": "..." }`
- API key must include `send` scope.
- Setup validation calls `/api/external/status`, so key should also include `modem_status` scope.

## Notes
- Phone number validation is done by gateway API.
- If no `target` is provided in notify call, integration uses configured default recipients.
