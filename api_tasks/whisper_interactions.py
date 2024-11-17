def create_transcripts_from_audio(client, transcript_suffix:str = '_transcript', local_folder:str=''):
    import os

    # Create a directory for transcripts if it doesn't exist
    transcript_dir = os.path.join(local_folder, 'transcripts')
    os.makedirs(transcript_dir, exist_ok=True)
    
    # Go through all files in the directory
    for filename in os.listdir(local_folder):
        # Skip if it's a directory or not an audio file
        if os.path.isdir(os.path.join(local_folder, filename)) or not filename.endswith(('.mp3', '.wav', '.m4a')):
            continue
            
        audio_path = os.path.join(local_folder, filename)
        transcript_path = os.path.join(transcript_dir, f"{os.path.splitext(filename)[0]}{transcript_suffix}.txt")
        
        # Skip if transcript already exists
        if os.path.exists(transcript_path):
            print(f"Transcript already exists for {filename}, skipping...")
            continue
            
        print(f"Processing {filename}...")
        
        try:
            with open(audio_path, "rb") as audio_file:
                # Call Whisper API
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                
                # Save transcript to file
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                    
                print(f"Transcript saved for {filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")