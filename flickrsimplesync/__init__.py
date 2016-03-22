import sys,os,argparse,json,re,urllib.request,html.parser,flickrapi

EXT_IMAGE = ('jpg', 'png', 'jpeg', 'gif', 'bmp')
EXT_VIDEO = ('avi', 'wmv', 'mov', 'mp4', '3gp', 'ogg', 'ogv', 'mts')

#  flickr api keys
KEY = 'f7da21662566bc773c7c750ddf7030f7'
SECRET = 'c329cdaf44c6d3f3'

def start_sync(sync_path, cmd_args, specific_path=None):
    is_windows = os.name == 'nt'
    is_download = cmd_args.download

    if not os.path.exists(sync_path):
        sys.stderr.write('Sync path does not exists')
        exit(0)

    # Common arguments
    args = {'format': 'json', 'nojsoncallback': 1}
    api = flickrapi.FlickrAPI(KEY, SECRET, cmd_args.username)  # pass username argument to api

    # Ask for permission
    token = api.authenticate_console(perms='write')
    args.update({'auth_token': token})

    # Get default user privacy preferences
    try:
        #Currently not handled in the flickrapi library
        privacypref = api.prefs_getPrivacy().getchildren()[0].attrib['privacy']
        # https://www.flickr.com/services/api/flickr.prefs.getPrivacy.html
    except:
        sys.stderr.write('Failed to get Flickr privacy preferences.')
        exit(1)

    #Default to private
    args.update({
        'is_public': 0,
        'is_friend': 0,
        'is_family': 0
    })

    #Update if so defined in preferences. Note that the privacy number is a string!
    if privacypref == '1':
        args.update({'is_public': 1})
    elif privacypref == '2':
        args.update({'is_friend': 1})
    elif privacypref == '3':
        args.update({'is_family': 1})
    elif privacypref == '4':
        args.update({'is_friend': 1,'is_family': 1})

    # Build your local photo sets
    photo_sets = {}
    skips_root = []
    for r, dirs, files in os.walk(sync_path if not specific_path else os.path.dirname(specific_path)):

        if cmd_args.starts_with and not r.startswith('{}{}'.format(sync_path, cmd_args.starts_with)):
            continue

        files = [f for f in files if not f.startswith('.')]
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if not file.startswith('.'):
                ext = file.lower().split('.').pop()
                if ext in EXT_IMAGE or \
                   ext in EXT_VIDEO:

                    if r == sync_path:
                        skips_root.append(file)
                    else:
                        photo_sets.setdefault(r, [])
                        photo_sets[r].append(file)

    if skips_root:
        print('To avoid disorganization on flickr sets root photos are not synced, skipped these photos: %s' % skips_root)
        print('Try to sync at top most level of your photos directory')

    # custom set builder
    def get_custom_set_title(path):
        title = path.split('/').pop()

        if cmd_args.custom_set:
            m = re.match(cmd_args.custom_set, path)
            if m:
                if not cmd_args.custom_set_builder:
                    title = '-'.join(m.groups())
                elif m.groupdict():
                    title = cmd_args.custom_set_builder.format(**m.groupdict())
                else:
                    title = cmd_args.custom_set_builder.format(*m.groups())
        return title

    # Get your photosets online and map it to your local
    html_parser = html.parser.HTMLParser()
    photosets_args = args.copy()
    page = 1
    photo_sets_map = {}

    # Show 3 possibilities
    if cmd_args.custom_set:
        for photo_set in photo_sets:
            print('Set Title: [%s]  Path: [%s]' % (get_custom_set_title(photo_set), photo_set))

        if input('Is this your expected custom set titles (y/n):') != 'y':
            exit(0)

    while True:
        print('Getting photosets page %s' % page)
        photosets_args.update({'page': page, 'per_page': 500})
        sets = json.loads(api.photosets_getList(**photosets_args).decode())
        page += 1
        if not sets['photosets']['photoset']:
            break

        for current_set in sets['photosets']['photoset']:
            # Make sure it's the one from backup format
            desc = str(html_parser.unescape(current_set['description']['_content']))
            if desc:
                photo_sets_map[desc] = current_set['id']
                title = get_custom_set_title(sync_path + desc)
                if cmd_args.update_custom_set and desc in photo_set and title != current_set['title']['_content']:
                    update_args = args.copy()
                    update_args.update({
                        'photoset_id': current_set['id'],
                        'title': title,
                        'description': desc
                    })
                    print('Updating custom title [%s]...' % title)
                    json.loads(api.photosets_editMeta(**update_args).decode())
                    print('done')

    print('Found %s photo sets' % len(photo_sets_map))

    # For adding photo to set
    def add_to_photo_set(photo_id, folder):
        # If photoset not found in online map create it else add photo to it
        # Always upload unix style
        if is_windows:
            folder = folder.replace(os.sep, '/')

        if folder not in photo_sets_map:
            photosets_args = args.copy()
            custom_title = get_custom_set_title(sync_path + folder)
            photosets_args.update({'primary_photo_id': photo_id,
                                   'title': custom_title,
                                   'description': folder})
            photo_set = json.loads(api.photosets_create(**photosets_args).decode())
            photo_sets_map[folder] = photo_set['photoset']['id']
            print('Created set [%s] and added photo' % custom_title)
        else:
            photosets_args = args.copy()
            photosets_args.update({'photoset_id': photo_sets_map.get(folder), 'photo_id': photo_id})
            result = json.loads(api.photosets_addPhoto(**photosets_args).decode())
            if result.get('stat') == 'ok':
                print('Success')
            else:
                sys.stderr.write(result)

    # Get photos in a set
    def get_photos_in_set(folder):
        photos = {}
        # Always upload unix style
        if is_windows:
            folder = folder.replace(os.sep, '/')

        if folder in photo_sets_map:
            photoset_args = args.copy()
            page = 1
            while True:
                photoset_args.update({'photoset_id': photo_sets_map[folder], 'page': page})
                if is_download:
                    photoset_args['extras'] = 'url_o,media'
                page += 1
                photos_in_set = json.loads(api.photosets_getPhotos(**photoset_args).decode())
                if photos_in_set['stat'] != 'ok':
                    break

                for photo in photos_in_set['photoset']['photo']:

                    if is_download and photo.get('media') == 'video':
                        # photo_args = args.copy()
                        # photo_args['photo_id'] = photo['id']
                        # sizes = json.loads(api.photos_getSizes(**photo_args))
                        # if sizes['stat'] != 'ok':
                        #     continue
                        #
                        # original = filter(lambda s: s['label'].startswith('Site') and s['media'] == 'video', sizes['sizes']['size'])
                        # if original:
                        #     photos[photo['title']] = original.pop()['source'].replace('/site/', '/orig/')
                        #     print photos
                        # Skipts download video for now since it doesn't work
                        continue
                    else:
                        photos[photo['title']] = photo['url_o'] if is_download else photo['id']

        return photos

    # If download mode lets skip upload but you can also modify this to your needs
    if is_download:
        # Download to corresponding paths
        os.chdir(sync_path)

        for photo_set in photo_sets_map:
            if photo_set and is_download == '.' or is_download != '.' and photo_set.startswith(is_download):
                folder = photo_set.replace(sync_path, '')
                print('Getting photos in set [%s]' % folder)
                photos = get_photos_in_set(folder)
                # If Uploaded on unix and downloading on windows & vice versa
                if is_windows:
                    folder = folder.replace('/', os.sep)

                if not os.path.isdir(folder):
                    os.makedirs(folder)

                for photo in photos:
                    # Adds skips
                    if cmd_args.ignore_images and photo.split('.').pop().lower() in EXT_IMAGE:
                        continue
                    elif cmd_args.ignore_videos and photo.split('.').pop().lower() in EXT_VIDEO:
                        continue

                    path = os.path.join(folder, photo)
                    if os.path.exists(path):
                        print('Skipped [%s] already downloaded' % path)
                    else:
                        print('Downloading photo [%s]' % path)
                        urllib.request.urlretrieve(photos[photo], os.path.join(sync_path, path))
    else:
        # Loop through all local photo set map and
        # upload photos that does not exists in online map
        for photo_set in sorted(photo_sets):
            folder = photo_set.replace(sync_path, '')
            display_title = get_custom_set_title(photo_set)
            #print(folder,photo_set,display_title)
            print('Getting photos in set [%s]' % display_title)
            photos = get_photos_in_set(folder)
            print('Found %s photos' % len(photos))

            for photo in sorted(photo_sets[photo_set]):
                # Adds skips
                if cmd_args.ignore_images and photo.split('.').pop().lower() in EXT_IMAGE:
                    continue
                elif cmd_args.ignore_videos and photo.split('.').pop().lower() in EXT_VIDEO:
                    continue

                if photo in photos or is_windows and photo.replace(os.sep, '/') in photos:
                    print('Skipped [%s] already exists in set [%s]' % (photo, display_title))
                else:
                    print('Uploading [%s] to set [%s]' % (photo, display_title))
                    upload_args = {
                        'auth_token': token,
                        # (Optional) The title of the photo.
                        'title': photo,
                        # (Optional) A description of the photo. May contain some limited HTML.
                        'description': folder,
                        # (Optional) Set to 0 for no, 1 for yes. Specifies who can view the photo.
                        'is_public': args['is_public'],
                        'is_friend': args['is_friend'],
                        'is_family': args['is_family'],
                        # (Optional) Set to 1 for Safe, 2 for Moderate, or 3 for Restricted.
                        'safety_level': 1,
                        # (Optional) Set to 1 for Photo, 2 for Screenshot, or 3 for Other.
                        'content_type': 1,
                        # (Optional) Set to 1 to keep the photo in global search results, 2 to hide from public searches.
                        'hidden': 2
                    }

                    file_path = os.path.join(photo_set, photo)
                    file_stat = os.stat(file_path)

                    if file_stat.st_size >= 1073741824:
                        sys.stderr.write('Skipped [%s] over size limit' % photo)
                        continue

                    try:
                        upload = api.upload(file_path, None, **upload_args)
                        photo_id = upload.find('photoid').text
                        add_to_photo_set(photo_id, folder)
                        photos[photo] = photo_id
                    except flickrapi.FlickrError as e:
                        sys.stderr.write(e)
                    except:
                        # todo add tracking to show later which ones failed
                        pass

    print('All Synced')

def main():
    parser = argparse.ArgumentParser(description='Sync current folder to your flickr account.')
    parser.add_argument('--starts-with', type=str, help='only sync that path that starts with')
    parser.add_argument('--download', type=str, help='download the photos from flickr specify a path or . for all')
    parser.add_argument('--ignore-videos', action='store_true', help='ignore video files')
    parser.add_argument('--ignore-images', action='store_true', help='ignore image files')
    parser.add_argument('-dir','--directory', type=str, default=os.getcwd(),
                        help='specify the sync folder (default is current dir)')
    parser.add_argument('--custom-set', type=str, help='customize your set name from path with regex')
    parser.add_argument('--custom-set-builder', type=str, help='build your custom set title (default just merge groups)')
    parser.add_argument('--update-custom-set', action='store_true', help='updates your set title from custom set')
    parser.add_argument('--username', type=str, help='token username') #token username argument for api

    args = parser.parse_args()

    start_sync(args.directory.rstrip(os.sep) + os.sep, args)
