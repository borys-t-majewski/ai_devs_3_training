def for_every_file_in(local_folder,supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.gif', '.webp', 'jfif')):
    import os
    list_of_paths = []
    for filename in os.listdir(local_folder):
        if filename.lower().endswith(supported_formats):
            list_of_paths.append(os.path.join(local_folder, filename))
    return list_of_paths

if __name__ == "__main__":
    print(for_every_file_in('C:\Projects\AI_DEVS_3\s_2_02_pictures'))