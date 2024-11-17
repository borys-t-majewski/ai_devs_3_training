final_answer = {'people': [
  'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\2024-11-12_report-00-sektor_C4.txt'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\2024-11-12_report-07-sektor_C4.txt'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\transcripts\\2024-11-12_report-10-sektor-C1.txt'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\transcripts\\2024-11-12_report-11-sektor-C2.txt'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\transcripts\\2024-11-12_report-11-sektor-C2_audio_convert.txt']
, 'hardware': [
  'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\2024-11-12_report-13.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\2024-11-12_report-15.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\2024-11-12_report-16.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\2024-11-12_report-17.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_2024-11-12_report-13.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_2024-11-12_report-15.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_2024-11-12_report-16.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_2024-11-12_report-17.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_processed_2024-11-12_report-13.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_processed_2024-11-12_report-15.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_processed_2024-11-12_report-16.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_processed_2024-11-12_report-17.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_images\\processed_processed_processed_2024-11-12_report-13.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_images\\processed_processed_processed_2024-11-12_report-15.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_images\\processed_processed_processed_2024-11-12_report-16.png'
, 'C:\\Projects\\AI_DEVS_3\\s_2_04_files\\processed_images\\processed_images\\processed_images\\processed_processed_processed_2024-11-12_report-17.png']
}

import os 

# print(final_answer)
trans = {}

for key in final_answer:
    for en,l in enumerate(final_answer[key]):
        final_answer[key][en] = os.path.split(l)[1].replace('_audio_convert.txt','.mp3')
    final_answer[key].sort()

print(final_answer)