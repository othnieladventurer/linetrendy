from django.shortcuts import render

# Create your views here.





def index(request):
    return render(request, 'linetrendy/index.html')



def shop(request):
    return render(request, 'linetrendy/shop.html')



def about(request):
    return render(request, 'linetrendy/about.html')


def contact(request):
    return render(request, 'linetrendy/contact.html')




