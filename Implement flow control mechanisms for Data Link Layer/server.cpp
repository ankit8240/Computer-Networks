#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <winsock2.h>

#pragma comment(lib, "ws2_32.lib")

using namespace std;
int count=0;
// --- Utility Function ---
bool CheckFCS(const vector<uint8_t> &frame)
{
    if (frame.size() < 5)
        return false;
    vector<uint8_t> data_part(frame.begin(), frame.end() - 4);
    uint32_t received_fcs = ((uint32_t)frame[frame.size() - 4] << 24) |
                            ((uint32_t)frame[frame.size() - 3] << 16) |
                            ((uint32_t)frame[frame.size() - 2] << 8) |
                            ((uint32_t)frame[frame.size() - 1]);

    uint32_t calculated_fcs = 0;
    for (uint8_t byte : data_part)
    {
        calculated_fcs += byte;
    }
    return calculated_fcs == received_fcs;
}

// --- Protocol Receiver Logic ---

// Stop-and-Wait Receiver
void run_stop_and_wait_receiver(SOCKET clientSocket)
{
    cout << "\nRunning Stop-and-Wait Receiver..." << endl;
    int expected_seq_num = 0;
    char buffer[1500];

    while (true)
    {
        int bytes = recv(clientSocket, buffer, sizeof(buffer), 0);
        if (bytes <= 0 || string(buffer, 3) == "END")
            break;

        vector<uint8_t> received_frame(buffer, buffer + bytes);
        int seq_num = received_frame[0];

        if (CheckFCS(received_frame))
        {
            if (seq_num == expected_seq_num)
            {
                count++;
                cout << "Frame " << seq_num << " received successfully. Sending ACK." << endl;
                string ack_msg = "ACK" + to_string(seq_num);
                send(clientSocket, ack_msg.c_str(), ack_msg.length(), 0);
                expected_seq_num = 1 - expected_seq_num;
            }
            else
            {
                count++;
                cout << "Duplicate frame " << seq_num << " received. Resending ACK for " << (1 - expected_seq_num) << "." << endl;
                string ack_msg = "ACK" + to_string(1 - expected_seq_num);
                send(clientSocket, ack_msg.c_str(), ack_msg.length(), 0);
            }
        }
        else
        {
            count++;
            cout << "Corrupted frame received. Discarding." << endl;
        }
    }
}

// Go-Back-N Receiver
void run_GoBackN_receiver(SOCKET clientSocket)
{
    cout << "\nRunning Go-Back-N Receiver..." << endl;
    int expected_seq_num = 0;
    char buffer[1500];

    while (true)
    {
        
        int bytes = recv(clientSocket, buffer, sizeof(buffer), 0);
        if (bytes <= 0 || string(buffer, 3) == "END")
            break;

        vector<uint8_t> received_frame(buffer, buffer + bytes);
        int seq_num = received_frame[0];

        if (CheckFCS(received_frame))
        {
            if (seq_num == expected_seq_num)
            {
                count++;
                cout << "In-order frame " << seq_num << " received. Sending cumulative ACK." << endl;
                expected_seq_num = (expected_seq_num + 1) % 256;
            }
            else
            {
                count++;
                cout << "Out-of-order frame " << seq_num << " received (expected " << expected_seq_num << "). Discarding." << endl;
            }
        }
        else
        {
            count++;
            cout << "Corrupted frame "<<seq_num<<" received. Discarding." << endl;
        }
        string ack_msg = "ACK" + to_string(expected_seq_num);
        send(clientSocket, ack_msg.c_str(), ack_msg.length(), 0);
    }
}

// Selective Repeat Receiver
void run_SelectiveRepeat_receiver(SOCKET clientSocket, int N)
{
    
    cout << "\nRunning Selective Repeat Receiver with N=" << N << "..." << endl;
    int rcv_base = 0;
    map<int, vector<uint8_t>> frame_buffer;
    char buffer[1500];

    while (true)
    {
        
        int bytes = recv(clientSocket, buffer, sizeof(buffer), 0);
        if (bytes <= 0 || string(buffer, 3) == "END")
            break;

        vector<uint8_t> received_frame(buffer, buffer + bytes);
        int seq_num = received_frame[0];

        if (CheckFCS(received_frame))
        {
            bool in_window = (seq_num >= rcv_base && seq_num < rcv_base + N);
            if (in_window)
            {
                count++;
                cout << "In-window frame " << seq_num << " received. Buffering and sending ACK." << endl;
                frame_buffer[seq_num] = received_frame;
                string ack_msg = "ACK" + to_string(seq_num);
                send(clientSocket, ack_msg.c_str(), ack_msg.length(), 0);

                while (frame_buffer.count(rcv_base))
                {
                    cout << "   -> Delivering frame " << rcv_base << " from buffer." << endl;
                    frame_buffer.erase(rcv_base);
                    rcv_base = (rcv_base + 1) % 256;
                }
                cout << "   -> Receiver window base is now: " << rcv_base << endl;
            }
            else if (seq_num >= rcv_base - N && seq_num < rcv_base)
            {
                count++;
                cout << "Old frame " << seq_num << " received. Resending ACK." << endl;
                string ack_msg = "ACK" + to_string(seq_num);
                send(clientSocket, ack_msg.c_str(), ack_msg.length(), 0);
            }
            else
            
            {
                count++;
                cout << "Frame " << seq_num << " outside window. Discarding." << endl;
            }
        }
        else
        {
            count++;
            cout << "Corrupted frame "<<seq_num<<" received. Discarding." << endl;
        }
    }
}

int main()
{
    // Winsock Init
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    // Socket Creation, Binding, Listening
    SOCKET serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(5248);
    bind(serverSocket, (sockaddr *)&serverAddr, sizeof(serverAddr));
    listen(serverSocket, 5);
    cout << "Server listening on port 5248..." << endl;

    // Accept Client
    SOCKET clientSocket = accept(serverSocket, NULL, NULL);
    cout << "Client connected." << endl;

    // Initial Handshake
    char setup_buffer[100];
    int bytes = recv(clientSocket, setup_buffer, sizeof(setup_buffer) - 1, 0);
    setup_buffer[bytes] = '\0';
    string setup_msg(setup_buffer);

    int protocol_choice = 0, N = 1;
    size_t p_pos = setup_msg.find("PROTOCOL:") + 9;
    size_t n_pos = setup_msg.find(",N:");
    protocol_choice = stoi(setup_msg.substr(p_pos, n_pos - p_pos));
    N = stoi(setup_msg.substr(n_pos + 3));
    send(clientSocket, "OK", 2, 0); // Acknowledge setup

    // Run selected protocol receiver
    switch (protocol_choice)
    {
    case 1:
        run_stop_and_wait_receiver(clientSocket);
        break;
    case 2:
        run_GoBackN_receiver(clientSocket);
        break;
    case 3:
        run_SelectiveRepeat_receiver(clientSocket, N);
        break;
    default:
        cerr << "Invalid protocol choice received." << endl;
    }

    cout << "\nClient finished transmission." << endl;
    // cout<<"Total Frames sent: "<<count<<endl;
    closesocket(clientSocket);
    closesocket(serverSocket);
    WSACleanup();
    return 0;
}