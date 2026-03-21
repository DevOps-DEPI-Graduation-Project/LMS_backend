import codecs

# Read the PowerShell-corrupted UTF-16 file
with codecs.open('backup.json', 'r', encoding='utf-16') as source_file:
    contents = source_file.read()

# Write a perfectly clean, standard UTF-8 file that Django expects
with codecs.open('backup_clean.json', 'w', encoding='utf-8') as target_file:
    target_file.write(contents)

print("Conversion complete! Your file is now clean UTF-8.")