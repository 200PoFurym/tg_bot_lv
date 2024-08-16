@router.message(F.photo, LeomatchRegistration.SEND_PHOTO)
async def handle_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'
    await save_media(message, state, file_url, "photo")


@router.message(F.video, LeomatchRegistration.SEND_PHOTO)
async def handle_video(message: types.Message, state: FSMContext):
    file_id = message.video.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'
    await save_media(message, state, file_url, "video")


async def save_media(message: types.Message, state: FSMContext, file_url: str, media_type: str):
    data = await state.get_data()
    user_id = message.from_user.id
    user = await User.get_or_none(user_id=user_id)

    if user:
        if media_type == "photo":
            user.profile_photo = file_url
        elif media_type == "video":
            user.profile_video = file_url
        await user.save()
    else:
        await User.create(
            user_id=user_id,
            profile_photo=file_url if media_type == "photo" else None,
            profile_video=file_url if media_type == "video" else None,
            **data
        )

    await message.answer(i18n.gettext("Регистрация завершена!"))
    await state.clear()

    @router.message(Command(commands=['start', 'help']))
    async def handle_start_and_help(message: types.Message, state: FSMContext):
        logger.info(f"Команда {message.text} получена.")
        try:
            user = await User.get_or_none(user_id=message.from_user.id)

            if message.text.startswith('/start'):
                # Начало регистрации, если состояние не установлено
                current_state = await state.get_state()
                if current_state is None:
                    await message.answer(i18n.gettext("Добро пожаловать! Давайте начнем регистрацию."),
                                         reply_markup=main_menu_kb())
                    await state.set_state(LeomatchRegistration.START)

                if user:
                    if not user.is_verified:
                        await message.reply(i18n.gettext(
                            "Рекомендуем пройти верификацию, чтобы другие пользователи доверяли вам больше."))

                    if not user.is_registered:
                        await message.reply(
                            i18n.gettext("Вы не завершили регистрацию. Давайте начнем с вашего возраста."),
                            reply_markup=main_menu_kb())
                        await state.set_state(LeomatchRegistration.AGE)
                    else:
                        await message.reply(i18n.gettext("Добро пожаловать обратно!"), reply_markup=main_menu_kb())
                else:
                    await message.reply(i18n.gettext("Вы не зарегистрированы. Давайте начнем с вашего возраста."),
                                        reply_markup=main_menu_kb())
                    await state.set_state(LeomatchRegistration.AGE)

            elif message.text.startswith('/help'):
                await message.reply(
                    i18n.gettext("Команда /help предоставляет информацию о том, как использовать бота."))

        except Exception as e:
            await message.reply(f"Ошибка в обработчике handle_start_and_help: {e}")


@router.message(Command(commands=["start"]))
async def handle_start(message: types.Message, state: FSMContext):
    referral_code = message.get_args().strip().upper()
    user_id = message.from_user.id

    # Проверьте, зарегистрирован ли пользователь
    user = await User.get_or_none(user_id=user_id)
    if user:
        await message.reply("Вы уже зарегистрированы.")
        return

    # Проверяем, существует ли реферальный код
    if referral_code:
        referrer = await User.get_or_none(referral_code=referral_code)
        if referrer:
            # Добавляем 20 дополнительных просмотров рефереру
            referrer.profile_views += 20
            referrer.views_expiry_date = datetime.now(timezone.utc) + timedelta(days=1)
            await referrer.save()
            await message.reply("Вы получили 20 дополнительных просмотров за использование реферального кода!")

    # Регистрируем нового пользователя
    await User.create(
        user_id=user_id,
        full_name=message.from_user.full_name,
        # другие данные пользователя...
    )
    await message.reply("Добро пожаловать! Вы успешно зарегистрированы.")

    @router.message(F.text.startswith(i18n.gettext("Мои подарки")))
    async def show_gifts(message: types.Message):
        user_id = message.from_user.id
        gifts = await Gift.filter(receiver_id=user_id).all()
        if not gifts:
            await message.reply(i18n.gettext("Вы не получали подарков."))
            return

        for gift in gifts:
            sender = await User.get(id=gift.sender_id)
            await bot.send_message(
                user_id,
                i18n.gettext(
                    "Подарок от {sender_name}\nТип: {gift_type}\nДата: {date_sent}\nМедиа: {media_url}").format(
                    sender_name=sender.full_name,
                    gift_type=gift.type,
                    date_sent=gift.date_sent.strftime('%Y-%m-%d %H:%M'),
                    media_url=gift.media_url
                )
            )

        def load_image_from_bytes(photo_bytes):
            np_arr = np.frombuffer(photo_bytes, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return image

        # Пример использования
        photo_bytes = ...  # ваши байты изображения
        image = load_image_from_bytes(photo_bytes)
        threshold_image = preprocess_image(image)

        if isinstance(photo_bytes, io.BytesIO):
            photo_bytes = photo_bytes.getvalue()
        photo_bytes = photo_bytes.getvalue() if isinstance(photo_bytes, io.BytesIO) else photo_bytes



# Загрузите изображение и преобразуйте его в черно-белое
image = cv2.imread('image.png')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
ret, thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY)

# Найдите контуры
contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Найдите контур с максимальной площадью
    max_contour = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(max_contour, returnPoints=False)

    if len(hull) > 3:
        defects = cv2.convexityDefects(max_contour, hull)
        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(max_contour[s][0])
                end = tuple(max_contour[e][0])
                far = tuple(max_contour[f][0])
                cv2.line(image, start, end, [0, 255, 0], 2)
                cv2.circle(image, far, 5, [0, 0, 255], -1)

# Отобразите результат
cv2.imshow('Image with Convexity Defects', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
