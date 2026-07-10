#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <chrono>
#include <map>
#include <winsock2.h>
#include <ctime>
#include <algorithm>
#include <iomanip> // For setprecision
#include<bits/stdc++.h>

#pragma comment(lib, "ws2_32.lib")

using namespace std;
using namespace std::chrono;

// --- Data Structures and Utility Functions ---

struct PerformanceMetrics
{
    string protocol_name;
    int window_size = 1;
    double error_prob = 0.0;
    long long total_time_ms = 0;
    int original_frames = 0;
    int total_frames_sent = 0;
    long long total_bytes = 0;
    double throughput_kbps = 0.0;
    double efficiency = 0.0;
};

void Channel(int error_type, double error_prob, vector<uint8_t> &frame)
{
    if (error_type == 0 || ((double)rand() / RAND_MAX) > error_prob)
        return;
    if (frame.size() < 6)
        return; // Not a valid frame to corrupt

    vector<uint8_t> data_part(frame.begin() + 1, frame.end() - 4);
    if (data_part.empty())
        return;

    if (error_type == 1)
    { // Single-bit error
        int byte_idx = rand() % data_part.size();
        int bit_idx = rand() % 8;
        data_part[byte_idx] ^= (1 << bit_idx);
    }

    vector<uint8_t> new_frame;
    new_frame.push_back(frame[0]);
    new_frame.insert(new_frame.end(), data_part.begin(), data_part.end());
    new_frame.insert(new_frame.end(), frame.end() - 4, frame.end());
    frame = new_frame;
}

vector<uint8_t> macToBytes(const string &mac)
{
    vector<uint8_t> bytes;
    for (unsigned int i = 0; i < mac.length(); i += 3)
    {
        string byteString = mac.substr(i, 2);
        bytes.push_back(static_cast<uint8_t>(stoi(byteString, nullptr, 16)));
    }
    return bytes;
}

uint32_t computeFCS(const vector<uint8_t> &data)
{
    uint32_t sum = 0;
    for (uint8_t byte : data)
    {
        sum += byte;
    }
    return sum;
}

vector<vector<uint8_t>> Framing(const vector<char> &fileData)
{
    const size_t PAYLOAD_SIZE = 100;
    string src_mac_str = "12:34:56:78:90:12", dst_mac_str = "AB:CD:EF:01:23:45";
    vector<uint8_t> src_mac = macToBytes(src_mac_str);
    vector<uint8_t> dst_mac = macToBytes(dst_mac_str);
    vector<vector<uint8_t>> all_frames;

    for (size_t i = 0; i < fileData.size(); i += PAYLOAD_SIZE)
    {
        size_t chunk_size = min(PAYLOAD_SIZE, fileData.size() - i);
        vector<uint8_t> payload(fileData.begin() + i, fileData.begin() + i + chunk_size);
        vector<uint8_t> header_and_payload;
        header_and_payload.insert(header_and_payload.end(), dst_mac.begin(), dst_mac.end());
        header_and_payload.insert(header_and_payload.end(), src_mac.begin(), src_mac.end());
        header_and_payload.push_back((uint8_t)(chunk_size >> 8));
        header_and_payload.push_back((uint8_t)(chunk_size & 0xFF));
        header_and_payload.insert(header_and_payload.end(), payload.begin(), payload.end());
        all_frames.push_back(header_and_payload);
    }
    return all_frames;
}

// --- Protocol Sender Logic (Full Implementations) ---

void run_stop_and_wait_sender(SOCKET sock, const vector<vector<uint8_t>> &frames, double error_prob, PerformanceMetrics &metrics)
{
    int seq_num = 0;
    DWORD timeout = 200;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout, sizeof(timeout));

    for (const auto &frame_data : frames)
    {
        bool ack_received = false;
        while (!ack_received)
        {
            vector<uint8_t> frame_with_header;
            frame_with_header.push_back((uint8_t)seq_num);
            frame_with_header.insert(frame_with_header.end(), frame_data.begin(), frame_data.end());

            uint32_t fcs = computeFCS(frame_with_header);
            frame_with_header.push_back((fcs >> 24) & 0xFF);
            frame_with_header.push_back((fcs >> 16) & 0xFF);
            frame_with_header.push_back((fcs >> 8) & 0xFF);
            frame_with_header.push_back(fcs & 0xFF);

            vector<uint8_t> frame_to_send = frame_with_header;
            Channel(1, error_prob, frame_to_send);

            send(sock, (const char *)frame_to_send.data(), frame_to_send.size(), 0);
            metrics.total_frames_sent++;

            char ack_buffer[10];
            int bytes = recv(sock, ack_buffer, sizeof(ack_buffer), 0);
            if (bytes > 0)
            {
                ack_buffer[bytes] = '\0';
                if (string(ack_buffer).find("ACK" + to_string(seq_num)) != string::npos)
                {
                    ack_received = true;
                }
            }
        }
        seq_num = 1 - seq_num;
    }
}

void run_GoBackN_sender(SOCKET sock, const vector<vector<uint8_t>> &frames, int N, double error_prob, PerformanceMetrics &metrics)
{
    int base = 0, next_seq_num = 0;
    int total_frames = frames.size();
    DWORD timeout = 1000;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout, sizeof(timeout));

    while (base < total_frames)
    {
        while (next_seq_num < base + N && next_seq_num < total_frames)
        {
            vector<uint8_t> frame_with_header;
            frame_with_header.push_back((uint8_t)(next_seq_num % 256));
            frame_with_header.insert(frame_with_header.end(), frames[next_seq_num].begin(), frames[next_seq_num].end());

            uint32_t fcs = computeFCS(frame_with_header);
            frame_with_header.push_back((fcs >> 24) & 0xFF);
            frame_with_header.push_back((fcs >> 16) & 0xFF);
            frame_with_header.push_back((fcs >> 8) & 0xFF);
            frame_with_header.push_back(fcs & 0xFF);

            vector<uint8_t> frame_to_send = frame_with_header;
            Channel(1, error_prob, frame_to_send);

            send(sock, (const char *)frame_to_send.data(), frame_to_send.size(), 0);
            metrics.total_frames_sent++;
            next_seq_num++;
        }

        char ack_buffer[50];
        int bytes = recv(sock, ack_buffer, sizeof(ack_buffer) - 1, 0);
        if (bytes > 0)
        {
            ack_buffer[bytes] = '\0';
            if (string(ack_buffer).rfind("ACK", 0) == 0)
            {
                try
                {
                    int ack_num = stoi(string(ack_buffer).substr(3));
                    if (ack_num > base)
                        base = ack_num;
                }
                catch (...)
                {
                }
            }
        }
        else
        {
            next_seq_num = base;
        }
    }
}

void run_SelectiveRepeat_sender(SOCKET sock, const vector<vector<uint8_t>> &frames, int N, double error_prob, PerformanceMetrics &metrics)
{
    int base = 0, next_seq_num = 0;
    int total_frames = frames.size();
    vector<bool> ack_status(total_frames, false);
    map<int, high_resolution_clock::time_point> sent_times;

    DWORD timeout = 1;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout, sizeof(timeout));

    while (base < total_frames)
    {
        while (next_seq_num < base + N && next_seq_num < total_frames)
        {
            vector<uint8_t> frame_with_header;
            frame_with_header.push_back((uint8_t)(next_seq_num % 256));
            frame_with_header.insert(frame_with_header.end(), frames[next_seq_num].begin(), frames[next_seq_num].end());

            uint32_t fcs = computeFCS(frame_with_header);
            frame_with_header.push_back((fcs >> 24) & 0xFF);
            frame_with_header.push_back((fcs >> 16) & 0xFF);
            frame_with_header.push_back((fcs >> 8) & 0xFF);
            frame_with_header.push_back(fcs & 0xFF);

            vector<uint8_t> frame_to_send = frame_with_header;
            Channel(1, error_prob, frame_to_send);

            send(sock, (const char *)frame_to_send.data(), frame_to_send.size(), 0);
            metrics.total_frames_sent++;
            sent_times[next_seq_num] = high_resolution_clock::now();
            next_seq_num++;
        }

        char ack_buffer[50];
        int bytes = recv(sock, ack_buffer, sizeof(ack_buffer) - 1, 0);
        if (bytes > 0)
        {
            ack_buffer[bytes] = '\0';
            if (string(ack_buffer).rfind("ACK", 0) == 0)
            {
                try
                {
                    int ack_num = stoi(string(ack_buffer).substr(3));
                    if (ack_num >= base && ack_num < next_seq_num && !ack_status[ack_num])
                    {
                        ack_status[ack_num] = true;
                        sent_times.erase(ack_num);
                    }
                }
                catch (...)
                {
                }
            }
        }

        while (base < total_frames && ack_status[base])
        {
            base++;
        }

        const int timeout_duration_ms = 250;
        auto current_time = high_resolution_clock::now();
        for (const auto &entry : sent_times)
        {
            auto seq = entry.first;
            auto start_time = entry.second;
            if (duration_cast<milliseconds>(current_time - start_time).count() > timeout_duration_ms)
            {
                vector<uint8_t> re_frame;
                re_frame.push_back((uint8_t)(seq % 256));
                re_frame.insert(re_frame.end(), frames[seq].begin(), frames[seq].end());
                uint32_t fcs = computeFCS(re_frame);
                re_frame.push_back((fcs >> 24) & 0xFF);
                re_frame.push_back((fcs >> 16) & 0xFF);
                re_frame.push_back((fcs >> 8) & 0xFF);
                re_frame.push_back(fcs & 0xFF);

                vector<uint8_t> frame_to_resend = re_frame;
                Channel(1, error_prob, frame_to_resend);
                send(sock, (const char *)frame_to_resend.data(), frame_to_resend.size(), 0);
                metrics.total_frames_sent++;
                sent_times[seq] = high_resolution_clock::now();
            }
        }
        Sleep(10);
    }
}

int main(int argc, char const *argv[])
{
    if (argc < 2)
    {
        cerr << "Usage: client <inputfile> [--csv]" << endl;
        return 1;
    }
    bool csv_output = (argc > 2 && string(argv[2]) == "--csv");
    srand(time(0));

    // File Reading
    ifstream file(argv[1], ios::binary);
    if (!file)
    {
        if (!csv_output)
            cerr << "Error opening file: " << argv[1] << endl;
        return 1;
    }
    vector<char> fileData((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    if (fileData.empty())
    {
        if (!csv_output)
            cerr << "Error: Input file is empty or could not be read." << endl;
        return 1;
    }

    // Winsock Init & Socket Connection
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(5248);
    serverAddr.sin_addr.s_addr = inet_addr("127.0.0.1");
    if (connect(sock, (sockaddr *)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
    {
        if (!csv_output)
            cerr << "Connection failed." << endl;
        closesocket(sock);
        WSACleanup();
        return 1;
    }
    if (!csv_output)
        cout << "Connected to server." << endl;

    // User Input
    int choice, N = 1;
    double error_prob = 0.0;
    if (!csv_output)
    {
        cout << "\nChoose Protocol:\n1. Stop-and-Wait\n2. Go-Back-N\n3. Selective Repeat\nEnter choice: ";
        cin >> choice;
        if (choice == 2 || choice == 3)
        {
            cout << "Enter window size (N): ";
            cin >> N;
        }
        cout << "Enter error probability (e.g., 0.0 for no error, 0.2 for 20%): ";
        cin >> error_prob;
    }
    else
    {
        cin >> choice >> N >> error_prob;
    }

    // Framing
    vector<vector<uint8_t>> frames = Framing(fileData);

    // Initial Handshake
    string setup_msg = "PROTOCOL:" + to_string(choice) + ",N:" + to_string(N);
    send(sock, setup_msg.c_str(), setup_msg.length(), 0);
    char ack_buf[10];
    recv(sock, ack_buf, sizeof(ack_buf), 0);

    // Run selected protocol and measure performance
    PerformanceMetrics metrics;
    metrics.original_frames = frames.size();
    metrics.total_bytes = fileData.size();
    metrics.window_size = N;
    metrics.error_prob = error_prob;

    auto start_time = high_resolution_clock::now();
    switch (choice)
    {
    case 1:
        metrics.protocol_name = "Stop-and-Wait";
        run_stop_and_wait_sender(sock, frames, error_prob, metrics);
        break;
    case 2:
        metrics.protocol_name = "Go-Back-N";
        run_GoBackN_sender(sock, frames, N, error_prob, metrics);
        break;
    case 3:
        metrics.protocol_name = "Selective Repeat";
        run_SelectiveRepeat_sender(sock, frames, N, error_prob, metrics);
        break;
    }
    auto end_time = high_resolution_clock::now();
    metrics.total_time_ms = duration_cast<milliseconds>(end_time - start_time).count();

    send(sock, "END", 3, 0);

    // Calculate and display metrics
    if (metrics.total_time_ms > 0)
    {
        metrics.throughput_kbps = (double)(metrics.total_bytes * 8 * 1000) / (metrics.total_time_ms * 1024);
    }
    if (metrics.total_frames_sent > 0)
    {
        metrics.efficiency = (double)metrics.original_frames / metrics.total_frames_sent;
    }

    if (csv_output)
    {
        cout << metrics.protocol_name << ","
             << metrics.window_size << ","
             << metrics.error_prob << ","
             << metrics.total_time_ms << ","
             << metrics.total_frames_sent << ","
             << fixed << setprecision(2) << metrics.throughput_kbps << ","
             << fixed << setprecision(4) << metrics.efficiency << endl;
    }
    else
    {
        cout << "\n--- Performance Metrics ---" << endl;
        cout << "Total Transmission Time: " << metrics.total_time_ms << " ms" << endl;
        cout << "Throughput: " << fixed << setprecision(2) << metrics.throughput_kbps << " Kbps" << endl;
        cout << "Total Frames Sent: " << metrics.total_frames_sent <<  endl;
        cout << "Protocol Efficiency: " << fixed << setprecision(2) << metrics.efficiency * 100 << "%" << endl;
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}