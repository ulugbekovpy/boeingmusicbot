import asyncio
import os
from aiohttp import web
from bot import dp, bot  # Твои импорты бота и диспетчера[cite: 3]

async def handle(request):
    return web.Response(text="Boeing Music is flying! ✈️")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передает порт в переменную PORT
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    # 1. Запускаем веб-сервер как ФОНОВУЮ задачу в Event Loop
    # Это не даст ему блокироваться поллингом бота
    asyncio.create_task(start_web_server())
    
    # Маленькая пауза, чтобы сервер успел инициализироваться и занять порт
    await asyncio.sleep(1)
    
    print("Bot is starting...")
    
    # 2. Запускаем поллинг бота
    # Сбрасываем ожидающие обновления, чтобы бот не отвечал на старый спам при запуске
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")