# include <bits/stdc++.h>
using namespace std;
int arr[10000];
int main(){
    int n;
    cin>>n;
    for (int i=1;i<=n;i++){
        cin>>arr[i];
    }for (int i=1;i<=n;i++){
        bool flag=0;
        for (int j=1;j<=n-i;j++){
            if (arr[j]>arr[j+1]){
                swap(arr[j],arr[j+1]);
                flag=1;
            }
        }
        if (!flag){
            break;
        }
        else{
            continue;
        }
    }for (int i=1;i<=n;i++){
        cout<<arr[i]<<" ";
    }
}