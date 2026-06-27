#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
using namespace std;

struct Student {
    string name;
    int score;
};

bool cmp(const Student &a, const Student &b) {
    return a.score > b.score; // 降序
}

int main() {
    int n;
    cin >> n;
    vector<Student> students(n);
    for (int i = 0; i < n; i++) {
        cin >> students[i].name >> students[i].score;
    }
    sort(students.begin(), students.end(), cmp);
    for (int i = 0; i < 5; i++) {
        cout << students[i].name << endl;
    }
    return 0;
}