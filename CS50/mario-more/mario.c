#include <cs50.h>
#include <stdio.h>

int main(void)
{
    int i;
    do
    {
        i = get_int("Height: ");
    }
    while (i < 1 || i > 8);
    //row
    for (int j = 0; j < i; j++)
    {
        for(int k = 0; k < i - j - 1; k++)
        {
            printf(" ");
        }
        //hash
        for (int l = 0; l <= j; l++)
        {
            //print hash
            printf("#");
        }
    printf("  ");
    for (int l = 0; l <= j; l++)
    {
        printf("#");
    }
    printf("\n");
    }
}