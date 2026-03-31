import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

async def get_media_info():
    try:
        sessions = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        current_session = sessions.get_current_session()
        
        if current_session:
            print("Session found!")
            print(f"Source: {current_session.source_app_user_model_id}")
            
            info = await current_session.try_get_media_properties_async()
            if info:
                print(f"Title: {info.title}")
                print(f"Artist: {info.artist}")
            else:
                print("No media properties found.")
                
            controls = current_session.get_playback_info()
            if controls:
                print(f"Status: {controls.playback_status}")
                
        else:
            print("No active media session. (Try playing a YouTube video)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_media_info())
