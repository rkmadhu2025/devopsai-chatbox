"""
Main Demo Runner for Context Engineering

Runs all context engineering demonstrations in sequence with a visual menu.
"""

import sys
import os
import json
from colorama import Fore, Style, init

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import print_header, print_section, print_success, print_info, print_error

# Initialize colorama
init(autoreset=True)


def check_config():
    """Check if config.json exists and is valid."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    if not os.path.exists(config_path):
        print_error("config.json not found!")
        print_info("Please copy config.example.json to config.json and add your OpenAI API key")
        print(f"\n{Fore.YELLOW}Steps:{Style.RESET_ALL}")
        print("1. Copy config.example.json to config.json")
        print("2. Edit config.json and replace 'your-openai-api-key-here' with your actual API key")
        print("3. Save and run this script again")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if config.get('api_key') == 'your-openai-api-key-here':
            print_error("Please update your API key in config.json")
            return False

        print_success("Configuration loaded successfully")
        print_info(f"Model: {config.get('model', 'gpt-3.5-turbo')}")
        return True

    except Exception as e:
        print_error(f"Error loading config: {e}")
        return False


def print_welcome():
    """Print welcome message."""
    print_header("CONTEXT ENGINEERING DEMO SUITE")

    print(f"{Fore.CYAN}Welcome to the Context Engineering demonstration!{Style.RESET_ALL}\n")

    print("This suite demonstrates four key context engineering techniques:")
    print(f"  {Fore.GREEN}1. WRITE{Style.RESET_ALL}    - Understanding context growth and token tracking")
    print(f"  {Fore.GREEN}2. SELECT{Style.RESET_ALL}   - Selective message passing and filtering")
    print(f"  {Fore.GREEN}3. COMPRESS{Style.RESET_ALL} - Context compression through summarization")
    print(f"  {Fore.GREEN}4. ISOLATE{Style.RESET_ALL}  - Maintaining separate conversation contexts")

    print(f"\n{Fore.YELLOW}Each demo is interactive and provides visual feedback!{Style.RESET_ALL}\n")


def print_menu():
    """Print the main menu."""
    print_section("DEMO MENU")

    print(f"{Fore.CYAN}[1]{Style.RESET_ALL} Demo 1: Context WRITE - Token Tracking & Growth")
    print(f"    See how context grows with each message and visualize token usage\n")

    print(f"{Fore.CYAN}[2]{Style.RESET_ALL} Demo 2: Context SELECT - Selective Message Passing")
    print(f"    Learn to filter relevant messages and reduce context size\n")

    print(f"{Fore.CYAN}[3]{Style.RESET_ALL} Demo 3: Context COMPRESS - Summarization Strategy")
    print(f"    Compress long conversations while preserving key information\n")

    print(f"{Fore.CYAN}[4]{Style.RESET_ALL} Demo 4: Context ISOLATE - Context Separation")
    print(f"    Maintain separate contexts for different tasks and domains\n")

    print(f"{Fore.CYAN}[5]{Style.RESET_ALL} Run All Demos (Sequential)")
    print(f"    Run all demonstrations one after another\n")

    print(f"{Fore.CYAN}[0]{Style.RESET_ALL} Exit\n")


def run_demo(demo_number):
    """Run a specific demo."""
    demos = {
        1: "demos/1_context_write.py",
        2: "demos/2_context_select.py",
        3: "demos/3_context_compress.py",
        4: "demos/4_context_isolate.py",
    }

    if demo_number not in demos:
        print_error("Invalid demo number")
        return

    demo_path = os.path.join(os.path.dirname(__file__), demos[demo_number])

    try:
        print_info(f"Running Demo {demo_number}...")
        print("=" * 80 + "\n")

        # Execute the demo
        with open(demo_path, 'r', encoding='utf-8') as f:
            code = f.read()
            exec(code, {'__name__': '__main__'})

        print("\n" + "=" * 80)
        print_success(f"Demo {demo_number} completed!")

    except Exception as e:
        print_error(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()


def run_all_demos():
    """Run all demos sequentially."""
    print_header("RUNNING ALL DEMOS")

    for demo_num in range(1, 5):
        input(f"\n{Fore.YELLOW}Press Enter to start Demo {demo_num}...{Style.RESET_ALL}")
        run_demo(demo_num)

        if demo_num < 4:
            print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Demo {demo_num} complete. Ready for Demo {demo_num + 1}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    print_header("ALL DEMOS COMPLETED")

    print(f"{Fore.GREEN}Congratulations!{Style.RESET_ALL} You've completed all context engineering demos.\n")

    print(f"{Fore.CYAN}Key Takeaways:{Style.RESET_ALL}")
    print("✓ Context management is crucial for LLM applications")
    print("✓ Different strategies serve different needs")
    print("✓ Token efficiency = cost savings")
    print("✓ Quality responses require thoughtful context design")

    print(f"\n{Fore.YELLOW}Next Steps:{Style.RESET_ALL}")
    print("• Experiment with your own use cases")
    print("• Combine multiple strategies for optimal results")
    print("• Monitor token usage in production")
    print("• Adapt strategies based on your specific needs")


def main():
    """Main entry point."""
    print_welcome()

    # Check configuration
    if not check_config():
        sys.exit(1)

    while True:
        print_menu()

        try:
            choice = input(f"{Fore.GREEN}Select an option (0-5): {Style.RESET_ALL}").strip()

            if choice == '0':
                print(f"\n{Fore.CYAN}Thank you for exploring Context Engineering!{Style.RESET_ALL}")
                print("Happy coding!\n")
                break

            elif choice in ['1', '2', '3', '4']:
                run_demo(int(choice))
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")

            elif choice == '5':
                run_all_demos()
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")

            else:
                print_error("Invalid choice. Please select 0-5.")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Exiting...{Style.RESET_ALL}\n")
            break

        except Exception as e:
            print_error(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
