# include <bits/stdc++.h>
using namespace std;
//十六进制转十进制
int main(){
    long long int ans = 0,cs=1;
    string n;
    cin >> n;
    for (int i=n.size()-1;i>=0;i--){
        if (n[i] >= '0' && n[i] <= '9'){
            ans += int(n[i]-'0')*cs;
        }
        else{
            ans += int(n[i]-'A'+10)*cs;
        }
        cs *= 16;
    }cout << ans << endl;
}