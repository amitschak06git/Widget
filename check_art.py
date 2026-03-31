import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
from winrt.windows.storage.streams import DataReader, IRandomAccessStreamReference

async def get_media_art():
    try:
        sessions = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        current_session = sessions.get_current_session()
        
        if current_session:
            print(f"Session: {current_session.source_app_user_model_id}")
            
            info = await current_session.try_get_media_properties_async()
            if info:
                print(f"Title: {info.title}")
                thumbnail = info.thumbnail
                if thumbnail:
                    print("Thumbnail reference found.")
                    stream_ref = await thumbnail.open_read_async()
                    size = stream_ref.size
                    print(f"Stream size: {size} bytes")
                    
                    if size > 0:
                        reader = DataReader(stream_ref.get_input_stream_at(0))
                        await reader.load_async(size)
                        
                        # Read bytes
                        data = bytes(reader.read_buffer(size))
                        print(f"Read {len(data)} bytes of image data.")
                        print(f"Header: {data[:10].hex()}")
                    
                else:
                    print("No thumbnail available.")
        else:
            print("No active media session.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_media_art())
