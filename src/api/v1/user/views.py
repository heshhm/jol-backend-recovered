class UserWalletUpdateAPIView(GenericAPIView):
    """ Increment or decrement user wallet coins
    CHOICES = (
        ('increment', 'Increment'),
        ('decrement', 'Decrement'),
    )
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoinSerializer

    #noinspection PyMethodMayBeStatic
    def post(self, request, *args, **kwargs):
        coins = request.data.get('coins')
        coin_type = request.data.get('type')
        user_wallet = request.user.get_wallet()

        try:
            if coin_type == 'increment':
                user_wallet.increment_coins(coins)
                return Response(
                    data={'message': 'Coins added successfully'},
                    status=status.HTTP_200_OK
                )
            elif coin_type == 'decrement':
                user_wallet.decrement_coins(coins)
                return Response(
                    data={'message': 'Coins deducted successfully'},
                    status=status.HTTP_200_OK
                )
            return Response(
                data={'error': 'Invalid coin type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserRetrieveChangeAPIView(RetrieveUpdateAPIView):
    """ Retrieve and update user account information """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """ Get the current authenticated user """
        return self.request.user

